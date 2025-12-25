# This file was generated automatically. Do not edit it directly.
from typing import Any, List, Literal, NotRequired, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class GetCohortsParams(TypedDict):
    projectId: str
    name: NotRequired[str]
    pageSize: NotRequired[float]
    nextPageToken: NotRequired[str]


class Query(TypedDict):
    """
    A query used to define a cohort
    """

    project: str
    queryType: str
    query: NotRequired[Any]


class Item(TypedDict):
    """
    Response body for a cohort
    """

    id: str
    name: str
    description: NotRequired[str]
    ownerProject: str
    resultCount: NotRequired[float]
    creatorUser: NotRequired[str]
    creationTime: NotRequired[str]
    queries: List[Query]
    subjectIds: List[str]


class Links(TypedDict):
    self: str
    next: NotRequired[str]


class GetCohortsResponse(TypedDict):
    """
    Response body for listing cohorts
    """

    items: List[Item]
    links: Links


class CreateCohortRequest(TypedDict):
    """
    Request body for creating or updating a cohort
    """

    name: str
    description: NotRequired[str]
    ownerProject: str
    queries: List[Query]


class CreateCohortResponse(TypedDict):
    """
    Response body for a cohort
    """

    id: str
    name: str
    description: NotRequired[str]
    ownerProject: str
    resultCount: NotRequired[float]
    creatorUser: NotRequired[str]
    creationTime: NotRequired[str]
    queries: List[Query]
    subjectIds: List[str]


class GetCohortResponse(TypedDict):
    """
    Response body for a cohort
    """

    id: str
    name: str
    description: NotRequired[str]
    ownerProject: str
    resultCount: NotRequired[float]
    creatorUser: NotRequired[str]
    creationTime: NotRequired[str]
    queries: List[Query]
    subjectIds: List[str]


class UpdateCohortRequest(TypedDict):
    """
    Request body for creating or updating a cohort
    """

    name: str
    description: NotRequired[str]
    ownerProject: str
    queries: List[Query]


class UpdateCohortResponse(TypedDict):
    """
    Response body for a cohort
    """

    id: str
    name: str
    description: NotRequired[str]
    ownerProject: str
    resultCount: NotRequired[float]
    creatorUser: NotRequired[str]
    creationTime: NotRequired[str]
    queries: List[Query]
    subjectIds: List[str]


class UpdateCohortPatientsRequest(TypedDict):
    subjectIds: List[str]
    action: Literal["ADD", "REMOVE"]


class UpdateCohortPatientsResponse(TypedDict):
    pass


class CohortsServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://cohorts-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def get_cohorts(self, params: GetCohortsParams):
        """Returns a list of cohorts that the user has access to."""
        res = await self.client.request(
            path="/v1/cohorts", method="GET", params=cast(dict, params)
        )
        return cast(AlphaResponse[GetCohortsResponse], res)

    async def create_cohort(self, body: CreateCohortRequest):
        """Create a cohort, representing a subset of a project based on one or more queries"""
        res = await self.client.request(
            path="/v1/cohorts", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[CreateCohortResponse], res)

    async def get_cohort(self, cohort_id: str):
        """Returns a cohort."""
        res = await self.client.request(
            path=f"/v1/cohorts/{quote(cohort_id)}", method="GET"
        )
        return cast(AlphaResponse[GetCohortResponse], res)

    async def update_cohort(self, cohort_id: str, body: UpdateCohortRequest):
        """Returns the updated cohort."""
        res = await self.client.request(
            path=f"/v1/cohorts/{quote(cohort_id)}",
            method="PATCH",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[UpdateCohortResponse], res)

    async def update_cohort_patients(
        self, project_id: str, cohort_id: str, body: UpdateCohortPatientsRequest
    ):
        """Adds or removes a patient from a cohort. Only works in the Fountain Life account + project."""
        res = await self.client.request(
            path=f"/v1/private/cohorts/projects/{quote(project_id)}/cohorts/{quote(cohort_id)}/patients",
            method="PATCH",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[UpdateCohortPatientsResponse], res)
