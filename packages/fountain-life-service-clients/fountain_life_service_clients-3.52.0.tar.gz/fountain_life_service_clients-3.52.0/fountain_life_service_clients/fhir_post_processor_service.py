# This file was generated automatically. Do not edit it directly.
from typing import Any, Literal, NotRequired, TypedDict, Union, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class Meta(TypedDict):
    tag: NotRequired[Any]


class Partial(TypedDict):
    meta: Meta


class GetPartialFhirResourceResponse1(TypedDict):
    id: str
    resourceType: Literal["DocumentReference"]
    partial: Partial


class partial(TypedDict):
    identifier: NotRequired[Any]


class GetPartialFhirResourceResponse2(TypedDict):
    id: str
    resourceType: Literal["Patient"]
    partial: partial


GetPartialFhirResourceResponse = Union[
    GetPartialFhirResourceResponse1, GetPartialFhirResourceResponse2
]


class FhirPostProcessorServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {
            "target": "lambda://fhir-post-processor-service:deployed",
            **(cfg or {}),
        }
        super().__init__(**kwargs)

    async def get_partial_fhir_resource(self, resource_type: str, id: str):
        res = await self.client.request(
            path=f"/v1/private/{quote(resource_type)}/{quote(id)}", method="GET"
        )
        return cast(AlphaResponse[GetPartialFhirResourceResponse], res)
