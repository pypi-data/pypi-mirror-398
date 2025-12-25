# This file was generated automatically. Do not edit it directly.
from typing import List, Literal, NotRequired, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class PrivateListOAuthAppsParams(TypedDict):
    nextPageToken: NotRequired[str]
    pageSize: NotRequired[str]
    origin: NotRequired[str]


class Theme(TypedDict):
    primaryColor: str
    textOnPrimaryColor: str
    backgroundImageUrl: NotRequired[str]
    disabledColor: NotRequired[str]


class SubjectInviteSettings(TypedDict):
    customEmailTemplateName: NotRequired[str]


class Item(TypedDict):
    account: str
    name: str
    description: str
    icon: NotRequired[str]
    headerImage: NotRequired[str]
    appUrl: str
    appType: Literal["standalone", "launched", "embedded"]
    clientId: str
    status: Literal["developing", "live"]
    termsLink: NotRequired[str]
    theme: NotRequired[Theme]
    addUserToGroups: NotRequired[List[str]]
    allowedOAuthScopes: List[str]
    allowedAccounts: List[str]
    callbackUrls: List[str]
    logoutUrls: List[str]
    confirmSignUpUrl: NotRequired[str]
    passwordlessLoginUrl: NotRequired[str]
    fromEmailAddress: NotRequired[str]
    subjectInviteSettings: NotRequired[SubjectInviteSettings]
    refreshTokenValidityDays: NotRequired[int]
    id: str
    lastUpdated: str


class Links(TypedDict):
    self: str
    next: NotRequired[str]


class PrivateListOAuthAppsResponse(TypedDict):
    items: List[Item]
    links: Links


class PrivateGetOAuthAppResponse(TypedDict):
    account: str
    name: str
    description: str
    icon: NotRequired[str]
    headerImage: NotRequired[str]
    appUrl: str
    appType: Literal["standalone", "launched", "embedded"]
    clientId: str
    status: Literal["developing", "live"]
    termsLink: NotRequired[str]
    theme: NotRequired[Theme]
    addUserToGroups: NotRequired[List[str]]
    allowedOAuthScopes: List[str]
    allowedAccounts: List[str]
    callbackUrls: List[str]
    logoutUrls: List[str]
    confirmSignUpUrl: NotRequired[str]
    passwordlessLoginUrl: NotRequired[str]
    fromEmailAddress: NotRequired[str]
    subjectInviteSettings: NotRequired[SubjectInviteSettings]
    refreshTokenValidityDays: NotRequired[int]
    id: str
    lastUpdated: str


class PrivateDeleteOAuthAppResponse(TypedDict):
    pass


class PrivateUpsertOAuthAppRequest(TypedDict):
    account: str
    name: str
    description: str
    icon: NotRequired[str]
    headerImage: NotRequired[str]
    appUrl: str
    appType: Literal["standalone", "launched", "embedded"]
    clientId: str
    status: Literal["developing", "live"]
    termsLink: NotRequired[str]
    theme: NotRequired[Theme]
    addUserToGroups: NotRequired[List[str]]
    allowedOAuthScopes: List[str]
    allowedAccounts: List[str]
    callbackUrls: List[str]
    logoutUrls: List[str]
    confirmSignUpUrl: NotRequired[str]
    passwordlessLoginUrl: NotRequired[str]
    fromEmailAddress: NotRequired[str]
    subjectInviteSettings: NotRequired[SubjectInviteSettings]
    refreshTokenValidityDays: NotRequired[int]


class PrivateUpsertOAuthAppResponse(TypedDict):
    account: str
    name: str
    description: str
    icon: NotRequired[str]
    headerImage: NotRequired[str]
    appUrl: str
    appType: Literal["standalone", "launched", "embedded"]
    clientId: str
    status: Literal["developing", "live"]
    termsLink: NotRequired[str]
    theme: NotRequired[Theme]
    addUserToGroups: NotRequired[List[str]]
    allowedOAuthScopes: List[str]
    allowedAccounts: List[str]
    callbackUrls: List[str]
    logoutUrls: List[str]
    confirmSignUpUrl: NotRequired[str]
    passwordlessLoginUrl: NotRequired[str]
    fromEmailAddress: NotRequired[str]
    subjectInviteSettings: NotRequired[SubjectInviteSettings]
    refreshTokenValidityDays: NotRequired[int]
    id: str
    lastUpdated: str


class PrivateGetByClientIdResponse(TypedDict):
    account: str
    name: str
    description: str
    icon: NotRequired[str]
    headerImage: NotRequired[str]
    appUrl: str
    appType: Literal["standalone", "launched", "embedded"]
    clientId: str
    status: Literal["developing", "live"]
    termsLink: NotRequired[str]
    theme: NotRequired[Theme]
    addUserToGroups: NotRequired[List[str]]
    allowedOAuthScopes: List[str]
    allowedAccounts: List[str]
    callbackUrls: List[str]
    logoutUrls: List[str]
    confirmSignUpUrl: NotRequired[str]
    passwordlessLoginUrl: NotRequired[str]
    fromEmailAddress: NotRequired[str]
    subjectInviteSettings: NotRequired[SubjectInviteSettings]
    refreshTokenValidityDays: NotRequired[int]
    id: str
    lastUpdated: str


class ListAppsParams(TypedDict):
    nextPageToken: NotRequired[str]
    pageSize: NotRequired[str]
    appType: NotRequired[Literal["standalone", "launched", "embedded"]]


class item(TypedDict):
    account: str
    name: str
    description: str
    icon: NotRequired[str]
    headerImage: NotRequired[str]
    appUrl: str
    appType: Literal["standalone", "launched", "embedded"]
    clientId: str
    status: Literal["developing", "live"]
    termsLink: NotRequired[str]
    theme: NotRequired[Theme]
    addUserToGroups: NotRequired[List[str]]
    allowedOAuthScopes: List[str]
    allowedAccounts: List[str]
    callbackUrls: List[str]
    logoutUrls: List[str]
    confirmSignUpUrl: NotRequired[str]
    passwordlessLoginUrl: NotRequired[str]
    fromEmailAddress: NotRequired[str]
    subjectInviteSettings: NotRequired[SubjectInviteSettings]
    refreshTokenValidityDays: NotRequired[int]
    id: str
    lastUpdated: str


class ListAppsResponse(TypedDict):
    items: List[item]
    links: Links


class OauthAppsServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://oauth-apps-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def private_list_o_auth_apps(self, params: PrivateListOAuthAppsParams):
        res = await self.client.request(
            path="/v1/private/oauth-apps", method="GET", params=cast(dict, params)
        )
        return cast(AlphaResponse[PrivateListOAuthAppsResponse], res)

    async def private_get_o_auth_app(self, id: str):
        res = await self.client.request(
            path=f"/v1/private/oauth-apps/{quote(id)}", method="GET"
        )
        return cast(AlphaResponse[PrivateGetOAuthAppResponse], res)

    async def private_delete_o_auth_app(self, id: str):
        res = await self.client.request(
            path=f"/v1/private/oauth-apps/{quote(id)}", method="DELETE"
        )
        return cast(AlphaResponse[PrivateDeleteOAuthAppResponse], res)

    async def private_upsert_o_auth_app(
        self, id: str, body: PrivateUpsertOAuthAppRequest
    ):
        res = await self.client.request(
            path=f"/v1/private/oauth-apps/{quote(id)}",
            method="PUT",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[PrivateUpsertOAuthAppResponse], res)

    async def private_get_by_client_id(self, client_id: str):
        res = await self.client.request(
            path=f"/v1/private/oauth-clients/{quote(client_id)}", method="GET"
        )
        return cast(AlphaResponse[PrivateGetByClientIdResponse], res)

    async def list_apps(self, params: ListAppsParams):
        res = await self.client.request(
            path="/v1/oauth-apps", method="GET", params=cast(dict, params)
        )
        return cast(AlphaResponse[ListAppsResponse], res)
