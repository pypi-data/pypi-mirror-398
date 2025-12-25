# This file was generated automatically. Do not edit it directly.
from typing import List, TypedDict, Unpack, cast

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)

VariantId = str


class GenerateHereditaryReportRequest(TypedDict):
    patientId: str
    variantSetId: str
    variantIds: List[VariantId]


class GenerateHereditaryReportResponse(TypedDict):
    pass


class GenomicsReportServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://genomics-report-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def generate_hereditary_report(self, body: GenerateHereditaryReportRequest):
        res = await self.client.request(
            path="/v1/v1/genomics-report/generate/hereditary",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[GenerateHereditaryReportResponse], res)
