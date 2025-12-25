# This file was generated automatically. Do not edit it directly.
from typing import List, Literal, NotRequired, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class ListFilesParams(TypedDict):
    name: NotRequired[str]
    orderBy: NotRequired[Literal["name", "size"]]
    pageSize: NotRequired[float]
    nextPageToken: NotRequired[str]
    datasetId: NotRequired[str]


class Item(TypedDict):
    id: str
    name: str
    datasetId: str
    contentType: str


class Links(TypedDict):
    self: str
    next: NotRequired[str]


class ListFilesResponse(TypedDict):
    items: List[Item]
    links: Links


class CreateFileRequest(TypedDict):
    id: str
    name: str
    datasetId: str
    contentType: str


class CreateFileResponse(TypedDict):
    id: str
    name: str
    datasetId: str
    contentType: str
    userId: str
    uploadUrl: str


class CreateFilePrivateRequest(TypedDict):
    id: str
    name: str
    datasetId: str
    contentType: str
    requiresMalwareScanning: NotRequired[bool]


class CreateFilePrivateResponse(TypedDict):
    id: str
    name: str
    datasetId: str
    contentType: str
    userId: str
    uploadUrl: str


class RetrieveFileParams(TypedDict):
    include: NotRequired[Literal["downloadUrl"]]
    includeContentDisposition: NotRequired[bool]


class RetrieveFileResponse(TypedDict):
    id: str
    name: str
    datasetId: str
    size: str
    contentType: str
    lastModified: str
    userId: str
    lrn: str
    downloadUrl: NotRequired[str]


class FileServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://file-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def list_files(self, params: ListFilesParams):
        """Lists the files for your LifeOmic account. Refine your results to a specific project with the *datasetId* query parameter. For more information, see [List Files](https://devcenter.docs.lifeomic.com/development/files#list-files)."""
        res = await self.client.request(
            path="/v1/files", method="GET", params=cast(dict, params)
        )
        return cast(AlphaResponse[ListFilesResponse], res)

    async def create_file(self, body: CreateFileRequest):
        """Creates and uploads a file. Uploading files is a two call operation. The first call is a POST call for a response that contains the presigned URL. The POST call contains JSON data for the file in the body. The second call is a PUT call to upload the file to the presigned URL. For more information, see [Upload Files](https://devcenter.docs.lifeomic.com/development/files#upload-files)."""
        res = await self.client.request(
            path="/v1/files", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[CreateFileResponse], res)

    async def create_file_private(self, body: CreateFilePrivateRequest):
        """Same as POST /files, but for private use, which has some extra capabilities."""
        res = await self.client.request(
            path="/v1/private/files", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[CreateFilePrivateResponse], res)

    async def retrieve_file(self, id: str, params: RetrieveFileParams):
        """Downloads a file. Add the file id from the general GET files response and the include parameter with the downloadUrl value. The response contains the download url. For more information, see [Download Files](https://devcenter.docs.lifeomic.com/development/files#download-files)."""
        res = await self.client.request(
            path=f"/v1/files/{quote(id)}", method="GET", params=cast(dict, params)
        )
        return cast(AlphaResponse[RetrieveFileResponse], res)

    async def delete_file(self, id: str):
        """Deletes the file specified with the file id."""
        await self.client.request(path=f"/v1/files/{quote(id)}", method="DELETE")
