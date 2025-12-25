# This file was generated automatically. Do not edit it directly.
from typing import Any, Dict, List, Literal, NotRequired, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class Tag(TypedDict):
    key: str
    value: str


class CreateFileRequest(TypedDict):
    id: NotRequired[str]
    name: str
    datasetId: str
    attributes: NotRequired[Dict[str, Any]]
    contentType: NotRequired[str]
    contentMD5: NotRequired[str]
    checksum: NotRequired[str]
    tags: NotRequired[List[Tag]]
    managedDocumentReference: NotRequired[bool]


class CreateFileResponse(TypedDict):
    id: str
    name: str
    datasetId: str
    attributes: NotRequired[Dict[str, Any]]
    contentType: NotRequired[str]
    contentMD5: NotRequired[str]
    checksum: NotRequired[str]
    tags: NotRequired[List[Tag]]
    userId: str
    uploadUrl: str


class UpdateFileRequest(TypedDict):
    name: NotRequired[str]
    attributes: NotRequired[Dict[str, Any]]
    checksum: NotRequired[str]
    managedDocumentReference: NotRequired[bool]


class UpdateFileResponse(TypedDict):
    id: str
    name: str
    datasetId: str
    attributes: NotRequired[Dict[str, Any]]
    contentType: NotRequired[str]
    contentMD5: NotRequired[str]
    checksum: NotRequired[str]
    tags: NotRequired[List[Tag]]
    userId: str


class GetFileByIdParams(TypedDict):
    subject: NotRequired[str]
    include: NotRequired[Literal["downloadUrl"]]
    includeContentDisposition: NotRequired[bool]


class GetFileByIdResponse(TypedDict):
    id: str
    name: str
    datasetId: str
    attributes: NotRequired[Dict[str, Any]]
    contentType: NotRequired[str]
    contentMD5: NotRequired[str]
    checksum: NotRequired[str]
    tags: NotRequired[List[Tag]]
    userId: str
    downloadUrl: NotRequired[str]


class Item(TypedDict):
    account: str
    dataset: str
    patient: str
    user: str
    date: str


class GetAllUserMappingsResponse(TypedDict):
    items: List[Item]


class GetPatientMappingResponse(TypedDict):
    patientId: str


class GetUserMappingResponse(TypedDict):
    items: List[str]


class PatientServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://patient-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def create_file(self, project_id: str, body: CreateFileRequest):
        """Create a new file in the project."""
        res = await self.client.request(
            path=f"/v1/fhir/files/projects/{quote(project_id)}/files",
            method="POST",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[CreateFileResponse], res)

    async def update_file(self, project_id: str, file_id: str, body: UpdateFileRequest):
        """Update an existing file."""
        res = await self.client.request(
            path=f"/v1/fhir/files/projects/{quote(project_id)}/files/{quote(file_id)}",
            method="PATCH",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[UpdateFileResponse], res)

    async def get_file_by_id(
        self, project_id: str, file_id: str, params: GetFileByIdParams
    ):
        """Get a file by its identifier."""
        res = await self.client.request(
            path=f"/v1/fhir/files/projects/{quote(project_id)}/files/{quote(file_id)}",
            method="GET",
            params=cast(dict, params),
        )
        return cast(AlphaResponse[GetFileByIdResponse], res)

    async def get_all_user_mappings(self, user_id: str):
        """Private endpoint to fetch all mappings for a given user. Not available via the public API."""
        res = await self.client.request(
            path=f"/private/patient-mappings/users/{quote(user_id)}", method="GET"
        )
        return cast(AlphaResponse[GetAllUserMappingsResponse], res)

    async def get_patient_mapping(self, project_id: str, user_id: str):
        """Private endpoint to fetch the single FHIR patient ID for a given user in a given project. Not available via the public API."""
        res = await self.client.request(
            path=f"/private/patient-mappings/projects/{quote(project_id)}/users/{quote(user_id)}",
            method="GET",
        )
        return cast(AlphaResponse[GetPatientMappingResponse], res)

    async def get_user_mapping(self, project_id: str, patient_id: str):
        """Private endpoint to fetch the platform user IDs for a given FHIR patient in a given project. Not available via the public API."""
        res = await self.client.request(
            path=f"/private/patient-mappings/projects/{quote(project_id)}/patients/{quote(patient_id)}",
            method="GET",
        )
        return cast(AlphaResponse[GetUserMappingResponse], res)
