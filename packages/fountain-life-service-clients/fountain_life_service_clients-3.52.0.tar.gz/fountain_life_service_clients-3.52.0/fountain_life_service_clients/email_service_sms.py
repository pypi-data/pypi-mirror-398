# This file was generated automatically. Do not edit it directly.
from typing import TypedDict, Unpack, cast

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class SendSmsRequest(TypedDict):
    messageId: str
    phoneNumber: str
    content: str


class SendSmsResponse(TypedDict):
    pass


class EmailServiceSmsClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://email-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def send_sms(self, body: SendSmsRequest):
        """Private endpoint for sending Fountain Life specific SMS."""
        res = await self.client.request(
            path="/v1/private/sendSms", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[SendSmsResponse], res)
