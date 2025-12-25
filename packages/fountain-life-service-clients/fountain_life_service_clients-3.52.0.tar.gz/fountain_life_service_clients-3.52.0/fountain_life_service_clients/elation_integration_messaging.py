# This file was generated automatically. Do not edit it directly.
from typing import List, NotRequired, Optional, TypedDict, Unpack, cast

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class SendCareTeamMessageRequest(TypedDict):
    patientId: str
    message: str
    urgent: NotRequired[bool]


class Patient(TypedDict):
    phcId: str
    elationId: str


class CareTeamMember(TypedDict):
    phcId: str
    elationId: Optional[str]
    userId: NotRequired[float]
    practice: NotRequired[float]


class SendCareTeamMessageResponse(TypedDict):
    patient: Patient
    careTeamMembers: List[CareTeamMember]
    message: str
    urgent: bool
    messageThreadId: float


class ElationIntegrationMessagingClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {
            "target": "lambda://elation-integration-messaging-api:deployed",
            **(cfg or {}),
        }
        super().__init__(**kwargs)

    async def send_care_team_message(self, body: SendCareTeamMessageRequest):
        """Send a message to a patient's care team"""
        res = await self.client.request(
            path="/v1/private/messages/careteam", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[SendCareTeamMessageResponse], res)
