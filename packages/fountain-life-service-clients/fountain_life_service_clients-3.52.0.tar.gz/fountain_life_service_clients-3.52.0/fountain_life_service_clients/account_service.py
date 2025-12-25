# This file was generated automatically. Do not edit it directly.
from typing import List, Literal, NotRequired, Optional, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class Account(TypedDict):
    id: str
    name: str
    owner: str
    type: Literal["FREE", "PAID", "ENTERPRISE"]


class ListAllAccountsResponse(TypedDict):
    accounts: List[Account]


class CreateAnAccountRequest(TypedDict):
    id: str
    name: str
    owner: str
    type: Literal["FREE", "PAID", "ENTERPRISE"]


class CreateAnAccountResponse(TypedDict):
    id: str
    name: str
    owner: str
    type: Literal["FREE", "PAID", "ENTERPRISE"]


class RetrieveAnAccountParams(TypedDict):
    include: NotRequired[Literal["groups"]]


class RetrieveAnAccountResponse(TypedDict):
    id: str
    name: str
    owner: str
    type: Literal["FREE", "PAID", "ENTERPRISE"]


class UpdateAnAccountRequest(TypedDict):
    name: NotRequired[str]
    deletionDate: NotRequired[Optional[str]]


class UpdateAnAccountResponse(TypedDict):
    id: str
    name: str
    owner: str
    type: Literal["FREE", "PAID", "ENTERPRISE"]


class DeleteAnAccountParams(TypedDict):
    force: NotRequired[bool]


class DeleteAnAccountResponse1(TypedDict):
    """
    The account object, or null if the account was not found/already deleted.
    """

    id: str
    name: str
    owner: str
    type: Literal["FREE", "PAID", "ENTERPRISE"]


DeleteAnAccountResponse = Optional[DeleteAnAccountResponse1]


class AccountServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://account-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def list_all_accounts(self):
        """Returns a list of accounts that the user has access to."""
        res = await self.client.request(path="/v1/accounts", method="GET")
        return cast(AlphaResponse[ListAllAccountsResponse], res)

    async def create_an_account(self, body: CreateAnAccountRequest):
        """Creates an account, returning the account object."""
        res = await self.client.request(
            path="/v1/accounts", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[CreateAnAccountResponse], res)

    async def retrieve_an_account(self, id: str, params: RetrieveAnAccountParams):
        """Retrieves details about an account. Returns the account object."""
        res = await self.client.request(
            path=f"/v1/accounts/{quote(id)}", method="GET", params=cast(dict, params)
        )
        return cast(AlphaResponse[RetrieveAnAccountResponse], res)

    async def update_an_account(self, id: str, body: UpdateAnAccountRequest):
        """Update an account by changing the name or clearing out a pending deletion date. Returns the account object."""
        res = await self.client.request(
            path=f"/v1/accounts/{quote(id)}", method="PATCH", body=cast(dict, body)
        )
        return cast(AlphaResponse[UpdateAnAccountResponse], res)

    async def delete_an_account(self, id: str, params: DeleteAnAccountParams):
        """Deletes an account. By default, the account will not be deleted for 14 days. During this time, the pending deletion can be cancelled by using the `PATCH` method. After the 14 day grace period, the account and all of its data will be removed."""
        res = await self.client.request(
            path=f"/v1/accounts/{quote(id)}", method="DELETE", params=cast(dict, params)
        )
        return cast(AlphaResponse[DeleteAnAccountResponse], res)
