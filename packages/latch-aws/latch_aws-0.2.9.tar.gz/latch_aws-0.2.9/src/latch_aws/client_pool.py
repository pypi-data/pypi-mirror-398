from asyncio import gather
from asyncio.locks import BoundedSemaphore
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from aiobotocore.config import AioConfig
from botocore.client import Config
from opentelemetry.trace import get_tracer
from types_aiobotocore_s3.client import S3Client

from .aws import AWSRegion, get_bucket_region, sess

tracer = get_tracer(__name__)


@dataclass
class RegionClientList:
    sema: BoundedSemaphore
    client_add_sema: BoundedSemaphore
    clients: list[S3Client]


class AsyncS3ClientPool:
    max_clients_per_region: int | None = None
    region_clients: dict[AWSRegion, RegionClientList] | None = None

    async def open(self, max_clients_per_region: int):
        with tracer.start_as_current_span(
            "open pool", attributes={"max_clients_per_region": max_clients_per_region}
        ):
            self.max_clients_per_region = max_clients_per_region
            self.region_clients = {}

    async def close(self):
        with tracer.start_as_current_span("close pool"):
            if self.max_clients_per_region is None or self.region_clients is None:
                raise RuntimeError("Pool not open")

            close_tasks = []
            for region_client in self.region_clients.values():
                for client in region_client.clients:
                    close_tasks.append(client.__aexit__(None, None, None))

            await gather(*close_tasks)
            self.region_clients = None
            self.max_clients_per_region = None

    @asynccontextmanager
    async def s3_client_for_bucket(
        self, bucket_name: str
    ) -> AsyncGenerator[S3Client, None]:
        if self.max_clients_per_region is None or self.region_clients is None:
            raise RuntimeError("Pool not open")

        with tracer.start_as_current_span(
            "s3 client for bucket", attributes={"bucket": bucket_name}
        ) as s:
            with tracer.start_as_current_span(
                "get bucket region", attributes={"bucket": bucket_name}
            ):
                region = await get_bucket_region(Bucket=bucket_name)

            s.set_attributes({"region": region})

            if region not in self.region_clients:
                self.region_clients[region] = RegionClientList(
                    sema=BoundedSemaphore(self.max_clients_per_region),
                    client_add_sema=BoundedSemaphore(1),
                    clients=[],
                )

            region_client = self.region_clients[region]

            async with region_client.sema:
                async with region_client.client_add_sema:
                    if len(region_client.clients) == 0:
                        with tracer.start_as_current_span(
                            "create s3 client",
                            attributes={"region": region},
                        ):
                            # https://github.com/boto/boto3/issues/421 - use addressing_style=path to support buckets before DNS propagation
                            client = await sess.create_client(
                                "s3",
                                region_name=region,
                                config=AioConfig().merge(
                                    Config(
                                        signature_version="s3v4",
                                        s3={"addressing_style": "path"},
                                        use_dualstack_endpoint=True,
                                    )
                                ),
                            ).__aenter__()
                    else:
                        client = region_client.clients.pop()

                try:
                    yield client
                finally:
                    region_client.clients.append(client)
                    s.set_attributes(
                        {
                            f"client_count_{region}": len(region_client.clients),
                            "region_count": len(self.region_clients)
                            if self.region_clients is not None
                            else 0,
                        }
                    )


s3_pool = AsyncS3ClientPool()
