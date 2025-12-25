# This file was generated automatically. Do not edit it directly.
from typing import List, NotRequired, TypedDict, Unpack, cast

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class Email(TypedDict):
    headerImage: str
    subject: str
    body: str
    buttonText: str
    buttonLink: str


class Notification(TypedDict):
    """
    A configuration for sending notifications about this prompt. If not provided, notifications will not be sent.
    """

    email: NotRequired[Email]


class Tag(TypedDict):
    system: NotRequired[str]
    code: NotRequired[str]


class CreateSchedulingPromptRequest(TypedDict):
    patientId: str
    practitionerId: str
    appointmentDisplayTitle: str
    calendarEventDisplayTitle: str
    notification: NotRequired[Notification]
    tags: NotRequired[List[Tag]]
    durationInMinutes: NotRequired[int]


class CreateSchedulingPromptResponse(TypedDict):
    pass


class MemberSchedulingServiceSchedulingPromptsClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {
            "target": "lambda://member-scheduling-service:deployed",
            **(cfg or {}),
        }
        super().__init__(**kwargs)

    async def create_scheduling_prompt(self, body: CreateSchedulingPromptRequest):
        res = await self.client.request(
            path="/v1/member-scheduling/scheduling-prompts",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[CreateSchedulingPromptResponse], res)
