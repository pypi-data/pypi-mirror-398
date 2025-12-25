# This file was generated automatically. Do not edit it directly.
from typing import List, Literal, NotRequired, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class Profile(TypedDict):
    email: str
    phoneNumber: NotRequired[str]
    familyName: str
    givenName: str
    name: str
    picture: str
    preferredUsername: str


class RetrieveCurrentUserResponse(TypedDict):
    id: str
    type: str
    profile: Profile


class profile(TypedDict):
    email: str
    familyName: str
    givenName: str
    name: str
    picture: str
    preferredUsername: str


class UpdateCurrentUserRequest(TypedDict):
    profile: profile


class Profile2(TypedDict):
    email: str
    phoneNumber: NotRequired[str]
    familyName: str
    givenName: str
    name: str
    picture: str
    preferredUsername: str


class UpdateCurrentUserResponse(TypedDict):
    id: str
    type: str
    profile: Profile2


class RetrieveAUserResponse(TypedDict):
    id: str
    type: str
    profile: Profile2


class RetrieveAUserPrivateResponse(TypedDict):
    id: str
    type: str
    profile: Profile2


class Item(TypedDict):
    account: str
    description: str
    id: str
    type: Literal["closed", "open"]


class Links(TypedDict):
    self: str
    next: NotRequired[str]


class ListUserGroupsResponse(TypedDict):
    items: List[Item]
    links: Links


class RetrieveUserPictureResponse(TypedDict):
    downloadUrl: str


class UpdateUserPictureRequest(TypedDict):
    pass


class UpdateUserPictureResponse(TypedDict):
    downloadUrl: str


class UserServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://user-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def retrieve_current_user(self):
        """Returns the full profile for the currently authenticated user"""
        res = await self.client.request(path="/v1/user", method="GET")
        return cast(AlphaResponse[RetrieveCurrentUserResponse], res)

    async def update_current_user(self, body: UpdateCurrentUserRequest):
        """Updates the authenticated user's profile"""
        res = await self.client.request(
            path="/v1/user", method="PATCH", body=cast(dict, body)
        )
        return cast(AlphaResponse[UpdateCurrentUserResponse], res)

    async def retrieve_a_user(self, username: str):
        """Returns a users profile. When requesting one's own profile the full profile is returned. Otherwise a limited profile is returned."""
        res = await self.client.request(
            path=f"/v1/users/{quote(username)}", method="GET"
        )
        return cast(AlphaResponse[RetrieveAUserResponse], res)

    async def retrieve_a_user_private(self, username: str):
        """Returns a users profile. Not available via the public API."""
        res = await self.client.request(
            path=f"/v1/private/users/{quote(username)}", method="GET"
        )
        return cast(AlphaResponse[RetrieveAUserPrivateResponse], res)

    async def list_user_groups(self, username: str):
        """Returns a list of groups that the user is a member of. This currently only succeeds if a user is asking for their own groups."""
        res = await self.client.request(
            path=f"/v1/users/{quote(username)}/groups", method="GET"
        )
        return cast(AlphaResponse[ListUserGroupsResponse], res)

    async def retrieve_user_picture(self, username: str):
        """Returns profile picture metadata."""
        res = await self.client.request(
            path=f"/v1/users/{quote(username)}/picture", method="GET"
        )
        return cast(AlphaResponse[RetrieveUserPictureResponse], res)

    async def update_user_picture(self, username: str, body: UpdateUserPictureRequest):
        """Update a user's profile picture. This only for the currently authorized user using a LifeOmic account."""
        res = await self.client.request(
            path=f"/v1/users/{quote(username)}/picture",
            method="PUT",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[UpdateUserPictureResponse], res)
