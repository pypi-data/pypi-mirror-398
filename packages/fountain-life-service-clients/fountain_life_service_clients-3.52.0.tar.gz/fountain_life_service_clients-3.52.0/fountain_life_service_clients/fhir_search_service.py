# This file was generated automatically. Do not edit it directly.
from typing import Any, Dict, List, Literal, NotRequired, TypedDict, Union, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class Expr(TypedDict):
    type: Literal["column_ref"]
    column: str
    table: NotRequired[str]


class Columns(TypedDict):
    expr: Expr


class columns(TypedDict):
    type: Literal["elasticsearch"]
    aggregations: Dict[str, Any]


class FromItem(TypedDict):
    table: str


class Where(TypedDict):
    type: Literal["elasticsearch"]
    query: Dict[str, Any]
    highlight: NotRequired[Dict[str, Any]]


class Limit(TypedDict):
    """
    A Response Offset
    """

    type: Literal["number"]
    value: float


class limit(TypedDict):
    """
    An Elasticsearch Search-After Clause
    """

    type: Literal["elasticsearch"]
    search_after: List


class LimitItem(TypedDict):
    """
    A Response Limit
    """

    type: Literal["number"]
    value: float


class OrderbyItem(TypedDict):
    type: Literal["ASC", "DESC"]
    expr: Expr


SearchProjectRequest = TypedDict(
    "SearchProjectRequest",
    {
        "type": Literal["select"],
        "columns": Union[Literal["*"], List[Union[Columns, columns]]],
        "from": List[FromItem],
        "where": NotRequired[Where],
        "limit": NotRequired[List[Union[Union[Limit, limit], LimitItem]]],
        "orderby": NotRequired[List[OrderbyItem]],
        "scroll": NotRequired[str],
    },
)


class Hit(TypedDict):
    _source: NotRequired[Any]
    sort: NotRequired[List]


class Hits(TypedDict):
    hits: List[Hit]


class SearchProjectResponse(TypedDict):
    hits: Hits
    _scroll_id: NotRequired[str]
    took: float
    timed_out: bool


class Columns2(TypedDict):
    expr: Expr


class Columns3(TypedDict):
    type: Literal["elasticsearch"]
    aggregations: Dict[str, Any]


class Limit2(TypedDict):
    """
    A Response Offset
    """

    type: Literal["number"]
    value: float


class Limit3(TypedDict):
    """
    An Elasticsearch Search-After Clause
    """

    type: Literal["elasticsearch"]
    search_after: List


class orderbyItem(TypedDict):
    type: Literal["ASC", "DESC"]
    expr: Expr


SearchPatientRequest = TypedDict(
    "SearchPatientRequest",
    {
        "type": Literal["select"],
        "columns": Union[Literal["*"], List[Union[Columns2, Columns3]]],
        "from": List[FromItem],
        "where": NotRequired[Where],
        "limit": NotRequired[List[Union[Union[Limit2, Limit3], LimitItem]]],
        "orderby": NotRequired[List[orderbyItem]],
    },
)


class hits(TypedDict):
    hits: List[Hit]


class SearchPatientResponse(TypedDict):
    hits: hits
    _scroll_id: NotRequired[str]
    took: float
    timed_out: bool


class Columns4(TypedDict):
    expr: Expr


class Columns5(TypedDict):
    type: Literal["elasticsearch"]
    aggregations: Dict[str, Any]


class Limit4(TypedDict):
    """
    A Response Offset
    """

    type: Literal["number"]
    value: float


class Limit5(TypedDict):
    """
    An Elasticsearch Search-After Clause
    """

    type: Literal["elasticsearch"]
    search_after: List


class OrderbyItem2(TypedDict):
    type: Literal["ASC", "DESC"]
    expr: Expr


SearchCohortRequest = TypedDict(
    "SearchCohortRequest",
    {
        "type": Literal["select"],
        "columns": Union[Literal["*"], List[Union[Columns4, Columns5]]],
        "from": List[FromItem],
        "where": NotRequired[Where],
        "limit": NotRequired[List[Union[Union[Limit4, Limit5], LimitItem]]],
        "orderby": NotRequired[List[OrderbyItem2]],
    },
)


class Hits2(TypedDict):
    hits: List[Hit]


class SearchCohortResponse(TypedDict):
    hits: Hits2
    _scroll_id: NotRequired[str]
    took: float
    timed_out: bool


class SearchDistinctRequest(TypedDict):
    field: str
    resource: str
    where: NotRequired[Dict[str, Any]]
    size: NotRequired[float]
    after: NotRequired[Dict[str, Any]]


class FhirSearchServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://fhir-search-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def search_project(self, project: str, body: SearchProjectRequest):
        """Search a project's FHIR resources using an expressive DSL"""
        res = await self.client.request(
            path=f"/v1/fhir-search/projects/{quote(project)}",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[SearchProjectResponse], res)

    async def search_patient(
        self, project: str, patient: str, body: SearchPatientRequest
    ):
        """Search a patient's FHIR resources using an expressive DSL"""
        res = await self.client.request(
            path=f"/v1/fhir-search/projects/{quote(project)}/patients/{quote(patient)}",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[SearchPatientResponse], res)

    async def search_cohort(self, project: str, cohort: str, body: SearchCohortRequest):
        """Search a cohort's FHIR resources using an expressive DSL"""
        res = await self.client.request(
            path=f"/v1/fhir-search/projects/{quote(project)}/cohorts/{quote(cohort)}",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[SearchCohortResponse], res)

    async def search_distinct(self, project: str, body: SearchDistinctRequest):
        """Fetch a distinct set of values for a given field belonging to a project's FHIR resources. Endpoint will programmatically optimize the search query"""
        res = await self.client.request(
            path=f"/v1/fhir-search/projects/{quote(project)}/distinct",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)
