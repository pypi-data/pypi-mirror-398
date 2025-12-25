# This file was generated automatically. Do not edit it directly.
from typing import List, Literal, NotRequired, TypedDict, Union, Unpack, cast

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class SendTemplatedNotificationRequest1(TypedDict):
    name: Literal["appointment-reminder"]
    appointmentId: str
    patientId: str
    messageId: str


class SendTemplatedNotificationRequest2(TypedDict):
    name: Literal["results-available"]
    type: str
    patientId: str
    messageId: str


class SendTemplatedNotificationRequest3(TypedDict):
    name: Literal["blood-work-scheduling-prompt"]
    procedureRequestId: str
    patientId: str
    messageId: str


class SendTemplatedNotificationRequest4(TypedDict):
    name: Literal["survey-reminder"]
    surveyNames: List[str]
    patientId: str
    messageId: str


SendTemplatedNotificationRequest = Union[
    SendTemplatedNotificationRequest1,
    SendTemplatedNotificationRequest2,
    SendTemplatedNotificationRequest3,
    SendTemplatedNotificationRequest4,
]


class SendTemplatedNotificationResponse(TypedDict):
    emailSent: bool
    smsSent: bool
    errors: NotRequired[List[str]]


class MemberNotificationServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {
            "target": "lambda://member-notification-service:deployed",
            **(cfg or {}),
        }
        super().__init__(**kwargs)

    async def send_templated_notification(self, body: SendTemplatedNotificationRequest):
        res = await self.client.request(
            path="/v1/private/notifications/templated",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[SendTemplatedNotificationResponse], res)
