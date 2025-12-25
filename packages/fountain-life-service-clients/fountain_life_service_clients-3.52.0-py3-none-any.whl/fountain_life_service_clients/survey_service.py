# This file was generated automatically. Do not edit it directly.
from typing import Any, List, Literal, NotRequired, TypedDict, Union, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class SurveyInvitationAcceptRequest(TypedDict):
    pass


class Invite(TypedDict):
    group: str


class Subject(TypedDict):
    id: str
    email: NotRequired[str]


class subject(TypedDict):
    firstName: str
    lastName: str
    address: str
    city: str
    state: str
    postalCode: str
    country: str
    email: str


class Response(TypedDict):
    status: NotRequired[
        Literal["in-progress", "completed", "amended", "entered-in-error", "stopped"]
    ]


class PostSurveyResponsesRequest(TypedDict):
    invite: NotRequired[Invite]
    survey: NotRequired[str]
    primarySurveyId: NotRequired[str]
    current: bool
    notificationType: NotRequired[Literal["EMAIL", "PUSH"]]
    autopopulate: NotRequired[bool]
    validateRequiredFieldsArePresent: NotRequired[bool]
    subject: Union[Subject, subject]
    response: NotRequired[Response]


class GetSurveyResponseParams(TypedDict):
    includeSurvey: NotRequired[bool]


class Subject2(TypedDict):
    reference: str
    display: str


class Questionnaire(TypedDict):
    reference: str
    display: str


class Author(TypedDict):
    reference: str


class PutSurveyResponseRequest(TypedDict):
    subject: Subject2
    questionnaire: Questionnaire
    resourceType: Literal["QuestionnaireResponse"]
    authored: str
    author: Author
    status: Literal["in-progress", "completed"]
    item: List


class AutopopulateSurveyResponseRequest(TypedDict):
    pass


class PutSurveyResponseAttachmentLinkRequest(TypedDict):
    fileName: str
    contentType: str


class GetSurveyResponseAttachmentParams(TypedDict):
    include: NotRequired[Literal["downloadUrl"]]
    includeContentDisposition: NotRequired[bool]


class PostSurveyRequest(TypedDict):
    resourceType: Literal["Questionnaire"]
    title: str
    status: Literal["draft", "active", "retried"]
    item: List


class PutSurveyRequest(TypedDict):
    resourceType: Literal["Questionnaire"]
    title: str
    status: Literal["draft", "active", "retried"]
    item: List


class PostSurveyAdapterRequest(TypedDict):
    pass


class PutSurveyAdapterByNameRequest(TypedDict):
    pass


class NotificationPreferences(TypedDict):
    email: bool
    push: bool


class PutSurveyConfigRequest(TypedDict):
    notificationPreferences: NotificationPreferences


class PostSurveyReminderRequest(TypedDict):
    pass


class PutSurveyScheduleRequest(TypedDict):
    recurrence: Literal["continuously", "daily", "weekly", "monthly", "yearly"]
    stopAfter: NotRequired[float]
    remind: NotRequired[bool]
    expire: NotRequired[bool]


class PostSurveyVersionRequest(TypedDict):
    resourceType: Literal["Questionnaire"]
    title: str
    status: Literal["draft", "active", "retried"]
    item: List


class SurveyServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://survey-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def survey_invitation_accept(
        self, id: str, body: SurveyInvitationAcceptRequest
    ):
        """Accept a survey invitation"""
        res = await self.client.request(
            path=f"/v1/survey-invitations/accept/{quote(id)}",
            method="PATCH",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)

    async def get_survey_responses(self, project_id: str):
        """Fetch survey responses in a project"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/responses", method="GET"
        )
        return cast(AlphaResponse[Any], res)

    async def post_survey_responses(
        self, project_id: str, body: PostSurveyResponsesRequest
    ):
        """Send survey to existing subject"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/responses",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)

    async def delete_survey_response(self, project_id: str, response_id: str):
        """Delete a survey response"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/responses/{quote(response_id)}",
            method="DELETE",
        )
        return cast(AlphaResponse[Any], res)

    async def get_survey_response(
        self, project_id: str, response_id: str, params: GetSurveyResponseParams
    ):
        """Fetch a survey response"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/responses/{quote(response_id)}",
            method="GET",
            params=cast(dict, params),
        )
        return cast(AlphaResponse[Any], res)

    async def put_survey_response(
        self, project_id: str, response_id: str, body: PutSurveyResponseRequest
    ):
        """Update a survey response"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/responses/{quote(response_id)}",
            method="PUT",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)

    async def autopopulate_survey_response(
        self, project_id: str, response_id: str, body: AutopopulateSurveyResponseRequest
    ):
        """Autopopulate a survey response based on configured rules"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/responses/{quote(response_id)}/autopopulate",
            method="PATCH",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)

    async def put_survey_response_attachment_link(
        self,
        project_id: str,
        response_id: str,
        link_id: str,
        body: PutSurveyResponseAttachmentLinkRequest,
    ):
        """Update a survey attachment link"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/responses/{quote(response_id)}/attachments/{quote(link_id)}",
            method="PUT",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)

    async def get_survey_response_attachment(
        self,
        project_id: str,
        response_id: str,
        link_id: str,
        file_id: str,
        params: GetSurveyResponseAttachmentParams,
    ):
        """Fetch a survey attachment"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/responses/{quote(response_id)}/attachments/{quote(link_id)}/{quote(file_id)}",
            method="GET",
            params=cast(dict, params),
        )
        return cast(AlphaResponse[Any], res)

    async def get_surveys(self, project_id: str):
        """Fetch surveys for a project"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys", method="GET"
        )
        return cast(AlphaResponse[Any], res)

    async def post_survey(self, project_id: str, body: PostSurveyRequest):
        """Create a survey for a project"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)

    async def get_survey_versions(self, project_id: str, primary_survey_id: str):
        """Fetch a prior survey version for a survey"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(primary_survey_id)}/versions",
            method="GET",
        )
        return cast(AlphaResponse[Any], res)

    async def delete_survey(self, project_id: str, survey_id: str):
        """Delete a survey"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}",
            method="DELETE",
        )
        return cast(AlphaResponse[Any], res)

    async def get_survey(self, project_id: str, survey_id: str):
        """Fetch a survey by ID"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}",
            method="GET",
        )
        return cast(AlphaResponse[Any], res)

    async def put_survey(self, project_id: str, survey_id: str, body: PutSurveyRequest):
        """Update a survey by ID"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}",
            method="PUT",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)

    async def get_survey_adapters(self, project_id: str, survey_id: str):
        """Fetch survey adapters configured for a survey"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/adapters",
            method="GET",
        )
        return cast(AlphaResponse[Any], res)

    async def post_survey_adapter(
        self, project_id: str, survey_id: str, body: PostSurveyAdapterRequest
    ):
        """Create a survey adapter for a survey"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/adapters",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)

    async def get_global_survey_adapter(self, project_id: str, survey_id: str):
        """Fetch global survey adapter"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/adapters/global",
            method="GET",
        )
        return cast(AlphaResponse[Any], res)

    async def delete_survey_adapter_by_name(
        self, project_id: str, survey_id: str, name: str
    ):
        """Delete survey adapter by name"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/adapters/{quote(name)}",
            method="DELETE",
        )
        return cast(AlphaResponse[Any], res)

    async def get_survey_adapter_by_name(
        self, project_id: str, survey_id: str, name: str
    ):
        """Fetch survey adapter by name"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/adapters/{quote(name)}",
            method="GET",
        )
        return cast(AlphaResponse[Any], res)

    async def put_survey_adapter_by_name(
        self,
        project_id: str,
        survey_id: str,
        name: str,
        body: PutSurveyAdapterByNameRequest,
    ):
        """Update survey adapter by name"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/adapters/{quote(name)}",
            method="PUT",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)

    async def get_survey_adapter_evaluation_by_name(
        self, project_id: str, survey_id: str, name: str
    ):
        """Evaluate (or test) a survey adapter by name"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/adapters/{quote(name)}/test",
            method="GET",
        )
        return cast(AlphaResponse[Any], res)

    async def get_survey_config(self, project_id: str, survey_id: str):
        """Get survey configuration for the survey ID"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/config",
            method="GET",
        )
        return cast(AlphaResponse[Any], res)

    async def put_survey_config(
        self, project_id: str, survey_id: str, body: PutSurveyConfigRequest
    ):
        """Update survey configuration for the survey ID"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/config",
            method="PUT",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)

    async def post_survey_reminder(
        self, project_id: str, survey_id: str, body: PostSurveyReminderRequest
    ):
        """Create a survey reminder"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/reminder",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)

    async def delete_survey_schedule(self, project_id: str, survey_id: str):
        """Delete a survey schedule"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/schedule",
            method="DELETE",
        )
        return cast(AlphaResponse[Any], res)

    async def get_survey_schedule(self, project_id: str, survey_id: str):
        """Fetch a survey schedule"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/schedule",
            method="GET",
        )
        return cast(AlphaResponse[Any], res)

    async def put_survey_schedule(
        self, project_id: str, survey_id: str, body: PutSurveyScheduleRequest
    ):
        """Update a survey schedule"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/schedule",
            method="PUT",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)

    async def post_survey_version(
        self, project_id: str, survey_id: str, body: PostSurveyVersionRequest
    ):
        """Create a new survey version for the existing survey by ID"""
        res = await self.client.request(
            path=f"/v1/survey/projects/{quote(project_id)}/surveys/{quote(survey_id)}/versions",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[Any], res)
