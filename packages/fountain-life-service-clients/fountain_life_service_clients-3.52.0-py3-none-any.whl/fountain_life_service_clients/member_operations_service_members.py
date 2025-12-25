# This file was generated automatically. Do not edit it directly.
from typing import Literal, NotRequired, TypedDict, Unpack, cast

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class OnboardMemberToAppRequest(TypedDict):
    patientId: str
    preferredContactMethod: NotRequired[Literal["email", "sms", "phone", "none"]]
    scheduleSurveyReminders: NotRequired[bool]
    skipOnboardingSurveys: NotRequired[bool]
    skipSecondaryConsents: NotRequired[bool]
    username: NotRequired[str]


class OnboardMemberToAppResponse(TypedDict):
    pass


class MemberOperationsServiceMembersClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {
            "target": "lambda://member-operations-service:deployed",
            **(cfg or {}),
        }
        super().__init__(**kwargs)

    async def onboard_member_to_app(self, body: OnboardMemberToAppRequest):
        res = await self.client.request(
            path="/v1/member-operations/members/onboard",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[OnboardMemberToAppResponse], res)
