# This file was generated automatically. Do not edit it directly.
from typing import List, Literal, NotRequired, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class Item(TypedDict):
    id: str
    name: str
    ehrType: str
    creator: NotRequired[str]
    apiBaseUrl: str
    apiAuthType: str
    ingestionModel: NotRequired[str]
    delayBetweenRecords: NotRequired[float]


class Links(TypedDict):
    self: str
    next: NotRequired[str]


class GetEhrsResponse(TypedDict):
    items: List[Item]
    links: Links


class CreateEhrRequest(TypedDict):
    id: NotRequired[str]
    name: str
    ehrType: str
    apiBaseUrl: str
    apiKey: str
    apiSecret: str
    apiAuthType: str
    ingestionModel: NotRequired[Literal["ASYNCHRONOUS", "SYNCHRONOUS"]]
    delayBetweenRecords: NotRequired[float]


class CreateEhrResponse(TypedDict):
    id: NotRequired[str]
    name: str
    ehrType: str
    apiBaseUrl: str
    apiKey: str
    apiSecret: str
    apiAuthType: str
    ingestionModel: NotRequired[Literal["ASYNCHRONOUS", "SYNCHRONOUS"]]
    delayBetweenRecords: NotRequired[float]


class GetEhrResponse(TypedDict):
    id: NotRequired[str]
    name: str
    ehrType: str
    apiBaseUrl: str
    apiKey: str
    apiSecret: str
    apiAuthType: str
    ingestionModel: NotRequired[Literal["ASYNCHRONOUS", "SYNCHRONOUS"]]
    delayBetweenRecords: NotRequired[float]


class UpdateEhrRequest(TypedDict):
    id: NotRequired[str]
    name: str
    ehrType: str
    apiBaseUrl: str
    apiKey: str
    apiSecret: str
    apiAuthType: str
    ingestionModel: NotRequired[Literal["ASYNCHRONOUS", "SYNCHRONOUS"]]
    delayBetweenRecords: NotRequired[float]


class UpdateEhrResponse(TypedDict):
    id: NotRequired[str]
    name: str
    ehrType: str
    apiBaseUrl: str
    apiKey: str
    apiSecret: str
    apiAuthType: str
    ingestionModel: NotRequired[Literal["ASYNCHRONOUS", "SYNCHRONOUS"]]
    delayBetweenRecords: NotRequired[float]


class item(TypedDict):
    id: str
    ehrId: str
    project: str


class GetConnectorsResponse(TypedDict):
    items: List[item]
    links: Links


class CreateConnectorRequest(TypedDict):
    id: str
    ehrId: str
    project: str


class CreateConnectorResponse(TypedDict):
    id: str
    ehrId: str
    project: str


class GetConnectorResponse(TypedDict):
    id: str
    ehrId: str
    project: str


class Connector(TypedDict):
    id: str
    ehrId: str
    project: str


class Record(TypedDict):
    type: str
    id: str


class Item2(TypedDict):
    connectors: List[Connector]
    records: List[Record]
    consumePendingUpdates: bool


class GetIngestionsResponse(TypedDict):
    items: List[Item2]
    links: Links


class CreateIngestionRequest(TypedDict):
    connectors: List[Connector]
    records: List[Record]
    consumePendingUpdates: bool


class CreateIngestionResponse(TypedDict):
    connectors: List[Connector]
    records: List[Record]
    consumePendingUpdates: bool


class GetIngestionResponse(TypedDict):
    connectors: List[Connector]
    records: List[Record]
    consumePendingUpdates: bool


class Ingestion(TypedDict):
    connectors: List[Connector]
    records: List[Record]
    consumePendingUpdates: bool


class Item3(TypedDict):
    ingestion: Ingestion
    cronExpression: str


class GetScheduledIngestionsResponse(TypedDict):
    items: List[Item3]
    links: Links


class ingestion(TypedDict):
    connectors: List[Connector]
    records: List[Record]
    consumePendingUpdates: bool


class CreateScheduledIngestionRequest(TypedDict):
    ingestion: ingestion
    cronExpression: str


class Ingestion2(TypedDict):
    connectors: List[Connector]
    records: List[Record]
    consumePendingUpdates: bool


class CreateScheduledIngestionResponse(TypedDict):
    ingestion: Ingestion2
    cronExpression: str


class Ingestion3(TypedDict):
    connectors: List[Connector]
    records: List[Record]
    consumePendingUpdates: bool


class GetScheduledIngestionResponse(TypedDict):
    ingestion: Ingestion3
    cronExpression: str


class EhrServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://ehr-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def get_ehrs(self):
        """Returns a list of EHRs that the user has access to."""
        res = await self.client.request(path="/v1/ehrs", method="GET")
        return cast(AlphaResponse[GetEhrsResponse], res)

    async def create_ehr(self, body: CreateEhrRequest):
        """Create an EHR configuration, which can then be connected to projects and used to sync data from your EHR to the LifeOmic Platform."""
        res = await self.client.request(
            path="/v1/ehrs", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[CreateEhrResponse], res)

    async def get_ehr(self, ehr_id: str):
        """Returns an EHR."""
        res = await self.client.request(path=f"/v1/ehrs/{quote(ehr_id)}", method="GET")
        return cast(AlphaResponse[GetEhrResponse], res)

    async def delete_ehr(self, ehr_id: str):
        """Deletes an EHR."""
        await self.client.request(path=f"/v1/ehrs/{quote(ehr_id)}", method="DELETE")

    async def update_ehr(self, ehr_id: str, body: UpdateEhrRequest):
        """Updates an EHR."""
        res = await self.client.request(
            path=f"/v1/ehrs/{quote(ehr_id)}", method="PUT", body=cast(dict, body)
        )
        return cast(AlphaResponse[UpdateEhrResponse], res)

    async def get_connectors(self, ehr_id: str):
        """Returns a list of project connectors configured for this EHR."""
        res = await self.client.request(
            path=f"/v1/ehrs/{quote(ehr_id)}/connectors", method="GET"
        )
        return cast(AlphaResponse[GetConnectorsResponse], res)

    async def create_connector(self, ehr_id: str, body: CreateConnectorRequest):
        """Creates an EHR project connector, which represents the ability for this EHR to tie ingested records to the connected project."""
        res = await self.client.request(
            path=f"/v1/ehrs/{quote(ehr_id)}/connectors",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[CreateConnectorResponse], res)

    async def get_connector(self, ehr_id: str, connector_id: str):
        """Returns an EHR project connector."""
        res = await self.client.request(
            path=f"/v1/ehrs/{quote(ehr_id)}/connectors/{quote(connector_id)}",
            method="GET",
        )
        return cast(AlphaResponse[GetConnectorResponse], res)

    async def delete_connector(self, ehr_id: str, connector_id: str):
        """Deletes the EHR project connector."""
        await self.client.request(
            path=f"/v1/ehrs/{quote(ehr_id)}/connectors/{quote(connector_id)}",
            method="DELETE",
        )

    async def get_ingestions(self, ehr_id: str):
        """Returns a list of EHR ingestions."""
        res = await self.client.request(
            path=f"/v1/ehrs/{quote(ehr_id)}/ingestions", method="GET"
        )
        return cast(AlphaResponse[GetIngestionsResponse], res)

    async def create_ingestion(self, ehr_id: str, body: CreateIngestionRequest):
        """Creates an EHR ingestion, which represents a synchronization of EHR data to the LifeOmic Platform."""
        res = await self.client.request(
            path=f"/v1/ehrs/{quote(ehr_id)}/ingestions",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[CreateIngestionResponse], res)

    async def get_ingestion(self, ehr_id: str, ingestion_id: str):
        """Returns an EHR ingestion."""
        res = await self.client.request(
            path=f"/v1/ehrs/{quote(ehr_id)}/ingestions/{quote(ingestion_id)}",
            method="GET",
        )
        return cast(AlphaResponse[GetIngestionResponse], res)

    async def get_scheduled_ingestions(self, ehr_id: str):
        """Returns a list of scheduled EHR ingestions."""
        res = await self.client.request(
            path=f"/v1/ehrs/{quote(ehr_id)}/scheduled-ingestions", method="GET"
        )
        return cast(AlphaResponse[GetScheduledIngestionsResponse], res)

    async def create_scheduled_ingestion(
        self, ehr_id: str, body: CreateScheduledIngestionRequest
    ):
        """Creates a recurring schedule on which an EHR ingestion should run."""
        res = await self.client.request(
            path=f"/v1/ehrs/{quote(ehr_id)}/scheduled-ingestions",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[CreateScheduledIngestionResponse], res)

    async def get_scheduled_ingestion(self, ehr_id: str, scheduled_ingestion_id: str):
        """Returns a scheduled EHR ingestion."""
        res = await self.client.request(
            path=f"/v1/ehrs/{quote(ehr_id)}/scheduled-ingestions/{quote(scheduled_ingestion_id)}",
            method="GET",
        )
        return cast(AlphaResponse[GetScheduledIngestionResponse], res)

    async def delete_scheduled_ingestion(
        self, ehr_id: str, scheduled_ingestion_id: str
    ):
        """Deletes the scheduled EHR ingestion."""
        await self.client.request(
            path=f"/v1/ehrs/{quote(ehr_id)}/scheduled-ingestions/{quote(scheduled_ingestion_id)}",
            method="DELETE",
        )
