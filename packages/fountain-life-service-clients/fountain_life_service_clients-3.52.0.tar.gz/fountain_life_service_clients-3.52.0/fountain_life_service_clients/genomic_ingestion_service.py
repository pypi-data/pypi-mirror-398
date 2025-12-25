# This file was generated automatically. Do not edit it directly.
from typing import TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class GetBroadInfoByGenomicsFileIdResponse(TypedDict):
    orderId: str
    sampleId: str


class GenomicIngestionServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {
            "target": "lambda://genomic-ingestion-service:deployed",
            **(cfg or {}),
        }
        super().__init__(**kwargs)

    async def get_broad_info_by_genomics_file_id(self, file_id: str):
        """Provide any genomics file id related to a patients broad genomic ingestion and get info to the originating Broad order"""
        res = await self.client.request(
            path=f"/v1/genomic-ingestion/broad/order/{quote(file_id)}", method="GET"
        )
        return cast(AlphaResponse[GetBroadInfoByGenomicsFileIdResponse], res)
