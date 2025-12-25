# This file was generated automatically. Do not edit it directly.
from typing import Any, Dict, List, NotRequired, Optional, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class ScheduledJob(TypedDict):
    id: NotRequired[str]
    workerId: str
    startTime: NotRequired[str]
    endTime: NotRequired[str]
    cronExpression: NotRequired[str]
    cronZone: NotRequired[str]
    targetDeliveryTime: NotRequired[str]
    jobPayload: Dict[str, Any]
    messageGroupId: NotRequired[str]


class CreateScheduledJobsRequest(TypedDict):
    scheduledJobs: List[ScheduledJob]
    jitterSourceField: NotRequired[str]
    jitterMaxDuration: NotRequired[float]


class CreateScheduledJobsResponse(TypedDict):
    scheduledJobs: List[ScheduledJob]


class GetScheduledJobResponse(TypedDict):
    id: str
    workerId: str
    startTime: NotRequired[str]
    endTime: NotRequired[str]
    cronExpression: NotRequired[str]
    cronZone: NotRequired[str]
    targetDeliveryTime: NotRequired[str]
    jobPayload: Dict[str, Any]
    messageGroupId: NotRequired[str]


class UpsertScheduledJobRequest(TypedDict):
    startTime: NotRequired[str]
    endTime: NotRequired[str]
    cronExpression: NotRequired[str]
    cronZone: NotRequired[str]
    targetDeliveryTime: NotRequired[str]
    jobPayload: Dict[str, Any]
    messageGroupId: NotRequired[str]


class UpsertScheduledJobResponse(TypedDict):
    id: NotRequired[str]
    workerId: str
    startTime: NotRequired[str]
    endTime: NotRequired[str]
    cronExpression: NotRequired[str]
    cronZone: NotRequired[str]
    targetDeliveryTime: NotRequired[str]
    jobPayload: Dict[str, Any]
    messageGroupId: NotRequired[str]


class ListScheduledJobsParams(TypedDict):
    targetDeliveryTimeStart: NotRequired[str]
    targetDeliveryTimeEnd: NotRequired[str]
    nextPageToken: NotRequired[str]
    pageSize: NotRequired[float]


class Item(TypedDict):
    id: str
    workerId: str
    startTime: NotRequired[str]
    endTime: NotRequired[str]
    cronExpression: NotRequired[str]
    cronZone: NotRequired[str]
    targetDeliveryTime: NotRequired[str]
    jobPayload: Dict[str, Any]
    messageGroupId: NotRequired[str]


class Links(TypedDict):
    self: str
    next: NotRequired[Optional[str]]


class ListScheduledJobsResponse(TypedDict):
    items: List[Item]
    links: Links


class SchedulerServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://scheduler-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def create_scheduled_jobs(self, body: CreateScheduledJobsRequest):
        """Create one or more scheduled jobs"""
        res = await self.client.request(
            path="/v1/private/scheduled-jobs", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[CreateScheduledJobsResponse], res)

    async def delete_scheduled_job(self, worker_id: str, id: str):
        """Delete a scheduled job by worker and id"""
        await self.client.request(
            path=f"/v1/private/{quote(worker_id)}/scheduled-jobs/{quote(id)}",
            method="DELETE",
        )

    async def get_scheduled_job(self, worker_id: str, id: str):
        """Get a scheduled job by worker and id"""
        res = await self.client.request(
            path=f"/v1/private/{quote(worker_id)}/scheduled-jobs/{quote(id)}",
            method="GET",
        )
        return cast(AlphaResponse[GetScheduledJobResponse], res)

    async def upsert_scheduled_job(
        self, worker_id: str, id: str, body: UpsertScheduledJobRequest
    ):
        """Upsert (create or update) a scheduled job"""
        res = await self.client.request(
            path=f"/v1/private/v2/{quote(worker_id)}/scheduled-jobs/{quote(id)}",
            method="PUT",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[UpsertScheduledJobResponse], res)

    async def list_scheduled_jobs(
        self, worker_id: str, params: ListScheduledJobsParams
    ):
        """List all scheduled jobs for a worker"""
        res = await self.client.request(
            path=f"/v1/private/{quote(worker_id)}/scheduled-jobs",
            method="GET",
            params=cast(dict, params),
        )
        return cast(AlphaResponse[ListScheduledJobsResponse], res)
