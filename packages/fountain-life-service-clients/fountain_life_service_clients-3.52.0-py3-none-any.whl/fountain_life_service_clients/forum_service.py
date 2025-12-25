# This file was generated automatically. Do not edit it directly.
from typing import (
    Any,
    Dict,
    List,
    Literal,
    NotRequired,
    Optional,
    TypedDict,
    Unpack,
    cast,
)

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class CreatePostRequest(TypedDict):
    id: NotRequired[str]
    message: str
    parentId: str
    metadata: NotRequired[str]
    parentType: Literal["CIRCLE", "PM_GROUP"]
    authorId: str
    rootParentId: str
    attachments: List[str]
    account: str
    systemGenerated: NotRequired[bool]


class CreatePostResponse(TypedDict):
    id: str
    message: NotRequired[Optional[str]]
    parentId: str
    authorId: NotRequired[Optional[str]]
    rootParentId: str
    attachments: List[str]
    systemGenerated: bool
    createdAt: float
    metadata: NotRequired[Optional[str]]
    originalPostId: str
    popularity: float
    priority: NotRequired[Optional[Literal["Announcement", "Standard"]]]
    replyCount: float
    status: Literal["DELETED", "ERROR", "PROCESSING", "READY", "UPLOADED", "UPLOADING"]
    blockedContent: NotRequired[Optional[bool]]
    lastModifiedAt: NotRequired[Optional[float]]
    reactionTotals: List[Dict[str, Any]]
    account: str
    deletedStatusAndCreatedAtAndPostId: str
    deletedStatusAndPriorityAndCreatedAtAndPostId: str


class ForumServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://forum-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def create_post(self, body: CreatePostRequest):
        """Create a post"""
        res = await self.client.request(
            path="/v1/private/forums/posts/post", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[CreatePostResponse], res)
