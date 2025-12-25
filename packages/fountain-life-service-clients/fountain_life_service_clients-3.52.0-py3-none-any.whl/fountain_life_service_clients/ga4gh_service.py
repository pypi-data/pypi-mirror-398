# This file was generated automatically. Do not edit it directly.
from typing import List, NotRequired, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class Sample(TypedDict):
    sampleId: str
    patientId: NotRequired[str]


class GetVariantSetResponse(TypedDict):
    id: str
    datasetId: str
    patientId: NotRequired[str]
    samples: NotRequired[List[Sample]]


class Ga4ghServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://ga4gh-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def get_variant_set(self, account: str, id: str):
        """Get a variant set by id"""
        res = await self.client.request(
            path=f"/{quote(account)}/v1/variantsets/{quote(id)}", method="GET"
        )
        return cast(AlphaResponse[GetVariantSetResponse], res)
