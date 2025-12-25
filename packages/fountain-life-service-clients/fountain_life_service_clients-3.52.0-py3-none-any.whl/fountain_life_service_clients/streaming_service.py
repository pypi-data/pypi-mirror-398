# This file was generated automatically. Do not edit it directly.
from typing import TypedDict, Unpack, cast

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class CreateTicketRequest(TypedDict):
    topic: str


class CreateTicketResponse(TypedDict):
    ticketId: str
    expiresIn: float


class StreamingServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://streaming-service-api:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def create_ticket(self, body: CreateTicketRequest):
        res = await self.client.request(
            path="/v1/streaming/stream", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[CreateTicketResponse], res)
