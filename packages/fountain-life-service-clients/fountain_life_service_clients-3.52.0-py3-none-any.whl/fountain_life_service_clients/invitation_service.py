# This file was generated automatically. Do not edit it directly.
from typing import List, Literal, NotRequired, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class RetrieveInvitationsParams(TypedDict):
    user: NotRequired[str]
    account: NotRequired[str]


class Item(TypedDict):
    id: str
    account: str
    accountName: str
    group: str
    groupName: str
    invitorUser: str
    email: str
    status: Literal["AWAITING-USER-ACTION", "ACCEPTED", "REJECTED", "REVOKED"]
    inviteTimestamp: str
    expirationTimestamp: str


class Links(TypedDict):
    self: str
    next: NotRequired[str]


class RetrieveInvitationsResponse(TypedDict):
    items: List[Item]
    links: Links


class InviteUserRequest(TypedDict):
    group: str
    email: str
    project: NotRequired[str]
    patient: NotRequired[str]


class InviteUserResponse(TypedDict):
    id: str
    account: str
    accountName: str
    group: str
    groupName: str
    invitorUser: str
    email: str
    status: Literal["AWAITING-USER-ACTION", "ACCEPTED", "REJECTED", "REVOKED"]
    inviteTimestamp: str
    expirationTimestamp: str


class UpdateInvitationRequest(TypedDict):
    status: Literal["ACCEPTED", "REJECTED", "REVOKED"]


class UpdateInvitationResponse(TypedDict):
    pass


class InvitationServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://invitation-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def retrieve_invitations(self, params: RetrieveInvitationsParams):
        """Retrieves the invitations to or from the session user."""
        res = await self.client.request(
            path="/v1/invitations", method="GET", params=cast(dict, params)
        )
        return cast(AlphaResponse[RetrieveInvitationsResponse], res)

    async def invite_user(self, body: InviteUserRequest):
        """Sends an email to a user, inviting them to join a group"""
        res = await self.client.request(
            path="/v1/invitations", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[InviteUserResponse], res)

    async def update_invitation(self, id: str, body: UpdateInvitationRequest):
        """Join, reject, or revoke an invitation."""
        res = await self.client.request(
            path=f"/v1/invitations/{quote(id)}", method="PATCH", body=cast(dict, body)
        )
        return cast(AlphaResponse[UpdateInvitationResponse], res)
