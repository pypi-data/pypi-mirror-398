# This file was generated automatically. Do not edit it directly.
from typing import (
    Any,
    Dict,
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


class InvokeBasicAgentRequest(TypedDict):
    input: str
    model_id: NotRequired[str]


class InvokeBasicAgentResponse(TypedDict):
    output: str


class InvokeHealthSummaryAgentRequest(TypedDict):
    version: Literal["v1", "v2"]
    subject_id: str
    project_id: str
    mutate: NotRequired[bool]
    should_extract_data: NotRequired[bool]
    should_include_synopsis_layout: NotRequired[bool]


class InvokeHealthSummaryAgentResponse(TypedDict):
    task_id: str


class GetHealthSummaryInvocationsParams(TypedDict):
    subject_id: str


class GetHealthSummaryInvocationsResponseItem(TypedDict):
    created: float
    expires: NotRequired[float]
    id: str
    scheduled: NotRequired[float]
    status: Literal[
        "scheduled", "pending", "processing", "failed", "completed", "expired"
    ]
    accountId: str
    agent: str
    agentInput: Dict[str, Any]
    subjectId: str


GetHealthSummaryInvocationsResponse = List[GetHealthSummaryInvocationsResponseItem]


class GetHealthSummaryScheduledTaskResponse(TypedDict):
    created: float
    expires: NotRequired[float]
    id: str
    scheduled: NotRequired[float]
    status: Literal[
        "scheduled", "pending", "processing", "failed", "completed", "expired"
    ]
    accountId: str
    agent: str
    agentInput: Dict[str, Any]
    subjectId: str


class FlushHealthSummaryScheduledTaskRequest(TypedDict):
    pass


class ProvideMessageFeedbackRequest(TypedDict):
    agent_name: str
    trace_id: str
    feedback: NotRequired[str]
    score: NotRequired[float]
    emoji: NotRequired[str]


class InvokeActionPlanNudgeRequest(TypedDict):
    account_id: str
    project_id: str
    subject_id: str
    user_id: str
    correlation_id: NotRequired[str]


class InvokeActionPlanNudgeResponse(TypedDict):
    subject_id: str
    nudge: Dict[str, Any]


class InvokeActionPlanRequest(TypedDict):
    subject_id: str
    project_id: str


class InvokeActionPlanResponse(TypedDict):
    task_id: str


class InvokeTemplateRequest(TypedDict):
    subject_id: str
    project_id: str
    template_id: str
    instructions: NotRequired[str]


class InvokeTemplateResponse(TypedDict):
    task_id: str


class GetAgentTokenResponse(TypedDict):
    AccessKeyId: str
    SecretAccessKey: str
    SessionToken: str
    Expiration: str


class ValidateFileOwnershipRequest(TypedDict):
    subject_id: str
    file_id: str
    project_id: str
    document_reference_id: str


class Result(TypedDict):
    status: Literal["valid", "invalid", "inconclusive"]
    reasoning: str


class ValidateFileOwnershipResponse(TypedDict):
    subject_id: str
    file_id: str
    document_reference_id: str
    result: Result


class Content(TypedDict):
    type: Literal["text"]
    text: str


class ImageUrl(TypedDict):
    url: str


class content(TypedDict):
    type: Literal["image_url"]
    image_url: ImageUrl


class References(TypedDict):
    value: str
    display: NotRequired[str]


class Metadata(TypedDict):
    day_of_diagnostics_date: NotRequired[Optional[str]]
    membership_tier: NotRequired[
        Optional[
            Literal["epic", "apex", "core", "core-v2", "edge", "health", "snap", "vita"]
        ]
    ]


class GetMemberContextResponse(TypedDict):
    content: List[Union[Content, content]]
    references: Optional[Dict[str, References]]
    metadata: NotRequired[Optional[Metadata]]


class CreateProviderTokenRequest(TypedDict):
    subject_id: str
    project_id: str
    voice_name: NotRequired[str]


class CreateProviderTokenResponse(TypedDict):
    name: str


class AgentsApiServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://agents-api-service-v2:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def invoke_basic_agent(self, body: InvokeBasicAgentRequest):
        """Invoke the basic agent"""
        res = await self.client.request(
            path="/v1/agents-v2/basic/invoke", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[InvokeBasicAgentResponse], res)

    async def invoke_health_summary_agent(self, body: InvokeHealthSummaryAgentRequest):
        """Invoke the health summary agent"""
        res = await self.client.request(
            path="/v1/agents-v2/health-summary/invoke",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[InvokeHealthSummaryAgentResponse], res)

    async def get_health_summary_invocations(
        self, params: GetHealthSummaryInvocationsParams
    ):
        """Get the health summary invocations"""
        res = await self.client.request(
            path="/v1/agents-v2/health-summary/invocations",
            method="GET",
            params=cast(dict, params),
        )
        return cast(AlphaResponse[GetHealthSummaryInvocationsResponse], res)

    async def get_health_summary_scheduled_task(self, task_id: str):
        """Get a health summary scheduled task"""
        res = await self.client.request(
            path=f"/v1/agents-v2/health-summary/invocations/{quote(task_id)}",
            method="GET",
        )
        return cast(AlphaResponse[GetHealthSummaryScheduledTaskResponse], res)

    async def flush_health_summary_scheduled_task(
        self, task_id: str, body: FlushHealthSummaryScheduledTaskRequest
    ):
        """Flush the health summary scheduled task so it is run immediately"""
        await self.client.request(
            path=f"/v1/agents-v2/health-summary/scheduled/{quote(task_id)}",
            method="PATCH",
            body=cast(dict, body),
        )

    async def provide_message_feedback(self, body: ProvideMessageFeedbackRequest):
        """Provide feedback on a message"""
        await self.client.request(
            path="/v1/agents-v2/feedback", method="POST", body=cast(dict, body)
        )

    async def invoke_action_plan_nudge(self, body: InvokeActionPlanNudgeRequest):
        """Invoke the action plan nudge agent"""
        res = await self.client.request(
            path="/v1/private/agents-v2/action-plan-nudge/invoke",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[InvokeActionPlanNudgeResponse], res)

    async def invoke_action_plan(self, body: InvokeActionPlanRequest):
        """Invoke the action plan agent"""
        res = await self.client.request(
            path="/v1/agents-v2/action-plan/invoke",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[InvokeActionPlanResponse], res)

    async def invoke_template(self, body: InvokeTemplateRequest):
        """Invoke the template agent"""
        res = await self.client.request(
            path="/v1/agents-v2/template-agent/invoke",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[InvokeTemplateResponse], res)

    async def get_agent_token(self):
        """Get an agent token for the current user"""
        res = await self.client.request(path="/v1/agents-v2/token", method="GET")
        return cast(AlphaResponse[GetAgentTokenResponse], res)

    async def validate_file_ownership(self, body: ValidateFileOwnershipRequest):
        """Validate file ownership"""
        res = await self.client.request(
            path="/v1/private/agents-v2/validate-ownership/invoke",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[ValidateFileOwnershipResponse], res)

    async def get_member_context(
        self, project_id: str, subject_id: str, context_type: str
    ):
        """Get structured member context for LLM initialization. Returns member health data context in a format suitable for initializing LLMs. Currently only 'structured' context type is supported."""
        res = await self.client.request(
            path=f"/v1/agents-v2/projects/{quote(project_id)}/subject/{quote(subject_id)}/member_context/{quote(context_type)}",
            method="GET",
        )
        return cast(AlphaResponse[GetMemberContextResponse], res)

    async def create_provider_token(
        self, provider_id: str, body: CreateProviderTokenRequest
    ):
        """Create an ephemeral provider token for the current user"""
        res = await self.client.request(
            path=f"/v1/agents-v2/providers/{quote(provider_id)}/token",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[CreateProviderTokenResponse], res)
