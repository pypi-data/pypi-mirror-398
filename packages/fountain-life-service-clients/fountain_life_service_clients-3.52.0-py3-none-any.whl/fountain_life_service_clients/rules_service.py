# This file was generated automatically. Do not edit it directly.
from typing import Any, Dict, List, Literal, NotRequired, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class GetRulesParams(TypedDict):
    datasetId: str
    inputType: NotRequired[Literal["event", "questionnaireResponse"]]
    eventType: NotRequired[Literal["PatientWriteEvent", "FileChangeEvent"]]
    resourceType: NotRequired[str]
    id: NotRequired[str]
    status: NotRequired[str]


class Input(TypedDict):
    """
    The input definition that will cause this rule to be executed.
    """

    type: Literal["event", "questionnaireResponse"]
    attributes: NotRequired[Any]


class GetRulesResponseItem(TypedDict):
    id: str
    account: str
    datasetId: str
    userId: str
    name: str
    description: NotRequired[str]
    creationTime: str
    updatedTime: str
    input: Input
    steps: List


GetRulesResponse = List[GetRulesResponseItem]


class CreateRuleRequest(TypedDict):
    id: str
    account: str
    datasetId: str
    userId: str
    name: str
    description: NotRequired[str]
    creationTime: str
    updatedTime: str
    input: Input
    steps: List


class CreateRuleResponse(TypedDict):
    id: str
    account: str
    datasetId: str
    userId: str
    name: str
    description: NotRequired[str]
    creationTime: str
    updatedTime: str
    input: Input
    steps: List


class GetRuleResponse(TypedDict):
    id: str
    account: str
    datasetId: str
    userId: str
    name: str
    description: NotRequired[str]
    creationTime: str
    updatedTime: str
    input: Input
    steps: List


class DeleteRuleResponse(TypedDict):
    pass


class GetRuleJobsParams(TypedDict):
    datasetId: str
    state: Literal["RUNNING", "COMPLETE", "CANCELED"]
    pageSize: NotRequired[float]
    nextPageToken: NotRequired[str]


class GetRuleJobsResponseItem(TypedDict):
    id: str
    creationTime: str
    userId: str
    account: str
    policy: Dict[str, Any]
    accountGroups: List[str]
    datasetId: str
    state: Literal["RUNNING", "COMPLETE", "CANCELED"]
    steps: List
    resourceType: Literal["Patient"]
    execution: str
    successes: float
    failures: float
    total: float


GetRuleJobsResponse = List[GetRuleJobsResponseItem]


class CreateRuleJobRequest(TypedDict):
    datasetId: str
    steps: List
    resourceType: Literal["Patient"]
    resourceIds: List[str]


class CreateRuleJobResponse(TypedDict):
    id: str
    creationTime: str
    userId: str
    account: str
    policy: Dict[str, Any]
    accountGroups: List[str]
    datasetId: str
    state: Literal["RUNNING", "COMPLETE", "CANCELED"]
    steps: List
    resourceType: Literal["Patient"]
    execution: str
    successes: float
    failures: float
    total: float


class GetRuleJobResponse(TypedDict):
    id: str
    creationTime: str
    userId: str
    account: str
    policy: Dict[str, Any]
    accountGroups: List[str]
    datasetId: str
    state: Literal["RUNNING", "COMPLETE", "CANCELED"]
    steps: List
    resourceType: Literal["Patient"]
    execution: str
    successes: float
    failures: float
    total: float


class DeleteRuleJobResponse(TypedDict):
    pass


class GetRuleJobItemsParams(TypedDict):
    state: NotRequired[Literal["PENDING", "RUNNING", "SUCCESS", "FAILURE"]]
    pageSize: NotRequired[float]
    nextPageToken: NotRequired[str]


class GetRuleJobItemsResponseItem(TypedDict):
    sequence: float
    account: str
    datasetId: str
    jobId: str
    state: str
    resourceId: str


GetRuleJobItemsResponse = List[GetRuleJobItemsResponseItem]


class RulesServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://rules-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def get_rules(self, params: GetRulesParams):
        """Returns a list of rules that the user has access to."""
        res = await self.client.request(
            path="/v1/rules", method="GET", params=cast(dict, params)
        )
        return cast(AlphaResponse[GetRulesResponse], res)

    async def create_rule(self, body: CreateRuleRequest):
        """Create a rule that will execute based on the given input, running each step in sequence until a step returns false, or all steps have completed. The input defines what causes the rule to fire."""
        res = await self.client.request(
            path="/v1/rules", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[CreateRuleResponse], res)

    async def get_rule(self, rule_id: str):
        """Returns a rule."""
        res = await self.client.request(
            path=f"/v1/rules/{quote(rule_id)}", method="GET"
        )
        return cast(AlphaResponse[GetRuleResponse], res)

    async def delete_rule(self, rule_id: str):
        """Deletes a rule."""
        res = await self.client.request(
            path=f"/v1/rules/{quote(rule_id)}", method="DELETE"
        )
        return cast(AlphaResponse[DeleteRuleResponse], res)

    async def get_rule_jobs(self, params: GetRuleJobsParams):
        """Returns a list of rule jobs that the user has access to."""
        res = await self.client.request(
            path="/v1/rules/jobs", method="GET", params=cast(dict, params)
        )
        return cast(AlphaResponse[GetRuleJobsResponse], res)

    async def create_rule_job(self, body: CreateRuleJobRequest):
        """Create a rule job that will execute the given steps for each of the given resource IDs. Rule jobs only support patient resources for now. The job will asynchronously execute the steps for each resource in batches, allowing it to handle large numbers of resources."""
        res = await self.client.request(
            path="/v1/rules/jobs", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[CreateRuleJobResponse], res)

    async def get_rule_job(self, job_id: str):
        """Returns a rule job."""
        res = await self.client.request(
            path=f"/v1/rules/jobs/{quote(job_id)}", method="GET"
        )
        return cast(AlphaResponse[GetRuleJobResponse], res)

    async def delete_rule_job(self, job_id: str):
        """Deletes a rule job."""
        res = await self.client.request(
            path=f"/v1/rules/jobs/{quote(job_id)}", method="DELETE"
        )
        return cast(AlphaResponse[DeleteRuleJobResponse], res)

    async def get_rule_job_items(self, job_id: str, params: GetRuleJobItemsParams):
        """Returns a a list of items for a rule job."""
        res = await self.client.request(
            path=f"/v1/rules/jobs/{quote(job_id)}/items",
            method="GET",
            params=cast(dict, params),
        )
        return cast(AlphaResponse[GetRuleJobItemsResponse], res)
