# This file was generated automatically. Do not edit it directly.
from typing import (
    Any,
    List,
    Literal,
    NotRequired,
    Optional,
    TypedDict,
    Union,
    Unpack,
    cast,
)
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class PageSize(TypedDict):
    pass


class GetResultsV3Params(TypedDict):
    pageSize: NotRequired[PageSize]
    nextPageToken: NotRequired[str]
    project: str
    resultCount: float
    cohort: NotRequired[str]
    includeClinicOnly: NotRequired[bool]
    source: NotRequired[Literal["mappedLabs", "unmappedLabs", "memberUpload"]]


class Coding(TypedDict):
    code: str
    system: str
    display: str


class System(TypedDict):
    code: str
    system: str
    display: NotRequired[str]


class SubSystem(TypedDict):
    code: str
    system: str
    display: NotRequired[str]


class Results(TypedDict):
    type: Literal["withoutRange"]
    status: Literal["default"]
    resource: NotRequired[Any]


class InRange(TypedDict):
    lower: NotRequired[float]
    upper: NotRequired[float]
    label: str
    status: Literal["in-range"]


class Optimal(TypedDict):
    """
    Currently this is always undefined. It may be used in the future.
    """

    lower: NotRequired[float]
    upper: NotRequired[float]
    label: str
    status: Literal["optimal"]


"""
Populated from reference ranges on the observation.
"""
Ranges = TypedDict(
    "Ranges",
    {
        "in-range": InRange,
        "optimal": NotRequired[Optimal],
    },
)


class results(TypedDict):
    type: Literal["withRange"]
    status: Literal["in-range", "attention", "optimal"]
    resource: NotRequired[Any]
    ranges: Ranges


class Results2(TypedDict):
    type: Literal["pending"]
    status: Literal["pending"]
    resource: NotRequired[Any]


class Item(TypedDict):
    coding: Coding
    systems: List[System]
    subSystems: List[SubSystem]
    results: List[Union[Union[Results, results], Results2]]


class Links(TypedDict):
    self: str
    next: NotRequired[Optional[Union[Any, str]]]


class GetResultsV3Response(TypedDict):
    items: List[Item]
    links: Links


class GetHistoryParams(TypedDict):
    pageSize: NotRequired[PageSize]
    nextPageToken: NotRequired[str]
    project: str
    code: str
    system: str
    cohort: NotRequired[str]
    includeClinicOnly: NotRequired[bool]
    source: NotRequired[Literal["mappedLabs", "memberUpload", "unmappedLabs"]]


class Attention(TypedDict):
    lower: NotRequired[float]
    upper: NotRequired[float]
    label: str
    status: Literal["attention"]


class optimal(TypedDict):
    lower: NotRequired[float]
    upper: NotRequired[float]
    label: str
    status: Literal["optimal"]


ranges = TypedDict(
    "ranges",
    {
        "in-range": InRange,
        "attention": NotRequired[Attention],
        "optimal": NotRequired[optimal],
    },
)


class Result(TypedDict):
    status: Literal["in-range", "attention", "optimal"]
    text: str
    interpretationText: str


class Items(TypedDict):
    type: Literal["withRange"]
    ranges: ranges
    result: Result
    coding: Coding
    resource: NotRequired[Any]
    systems: List[System]
    subSystems: List[SubSystem]
    aboutText: str


class result(TypedDict):
    status: Literal["default"]
    text: str
    interpretationText: str


class items(TypedDict):
    type: Literal["withoutRange"]
    result: result
    coding: Coding
    resource: NotRequired[Any]
    systems: List[System]
    subSystems: List[SubSystem]
    aboutText: str


class Result2(TypedDict):
    status: Literal["pending"]


class Items2(TypedDict):
    type: Literal["pending"]
    result: Result2
    coding: Coding
    resource: NotRequired[Any]
    systems: List[System]
    subSystems: List[SubSystem]
    aboutText: str


class GetHistoryResponse(TypedDict):
    items: List[Union[Union[Items, items], Items2]]
    links: Links


class MedicalResultsServiceResultsClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://medical-results-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def get_results_v3(self, patient_id: str, params: GetResultsV3Params):
        res = await self.client.request(
            path=f"/v1/medical-results/v3/patient/{quote(patient_id)}/results",
            method="GET",
            params=cast(dict, params),
        )
        return cast(AlphaResponse[GetResultsV3Response], res)

    async def get_history(self, patient_id: str, params: GetHistoryParams):
        res = await self.client.request(
            path=f"/v1/medical-results/patient/{quote(patient_id)}/history",
            method="GET",
            params=cast(dict, params),
        )
        return cast(AlphaResponse[GetHistoryResponse], res)
