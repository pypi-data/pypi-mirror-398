# This file was generated automatically. Do not edit it directly.
from typing import List, Literal, NotRequired, TypedDict, Unpack, cast

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class PrivateListDomainsParams(TypedDict):
    domain: str
    pageSize: NotRequired[str]
    nextPageToken: NotRequired[str]


class Basic(TypedDict):
    """
    State of basic functionality of a claimed domain such as SSO login suggestions.
    """

    status: Literal["verified", "unverified"]


class Email(TypedDict):
    """
    State of being able to send messages from an email address of the domain.
    """

    status: Literal["verified", "unverified"]


class Verifications(TypedDict):
    """
    Describes the current state of the claimed domain's verifications.
    """

    basic: Basic
    email: Email


class Item(TypedDict):
    account: str
    domain: str
    eligibleForLoginMethods: bool
    verifications: Verifications


class Links(TypedDict):
    self: str
    next: NotRequired[str]


class PrivateListDomainsResponse(TypedDict):
    items: List[Item]
    links: Links


class ClaimedDomainsServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://claimed-domains-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def private_list_domains(self, params: PrivateListDomainsParams):
        res = await self.client.request(
            path="/v1/private/claimed-domains", method="GET", params=cast(dict, params)
        )
        return cast(AlphaResponse[PrivateListDomainsResponse], res)
