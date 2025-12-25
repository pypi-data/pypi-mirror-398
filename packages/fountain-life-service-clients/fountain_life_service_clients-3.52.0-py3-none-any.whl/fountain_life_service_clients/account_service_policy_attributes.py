# This file was generated automatically. Do not edit it directly.
from typing import Any, Dict, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class PolicyAttributesObject(TypedDict):
    attributes: Dict[str, Any]


class AccountServicePolicyAttributesClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://account-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def update_policy_attributes_for_user(
        self, username: str, body: PolicyAttributesObject
    ):
        """Updates the policy attributes for the specified user, returning the updated
        attributes.

        Using this API requires access to the `accessAdmin` operation.
        """
        res = await self.client.request(
            path=f"/v1/policy-attributes/users/{quote(username)}",
            method="PUT",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[PolicyAttributesObject], res)

    async def get_policy_attributes_for_user(self, username: str):
        """Fetches the policy attributes for the specified user.

        Using this API requires access to the `accessAdmin` operation.
        """
        res = await self.client.request(
            path=f"/v1/policy-attributes/users/{quote(username)}", method="GET"
        )
        return cast(AlphaResponse[PolicyAttributesObject], res)
