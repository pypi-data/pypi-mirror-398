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


class Attachment(TypedDict):
    filename: str
    content: str
    contentType: str


class SendMailRequest(TypedDict):
    email: str
    expirationDateTime: str
    language: NotRequired[Optional[str]]
    messageId: str
    priority: Literal["HIGH", "LOW"]
    source: NotRequired[str]
    replyToAddresses: NotRequired[List[str]]
    attachments: NotRequired[List[Attachment]]
    account: NotRequired[str]
    subject: str
    html: str
    text: NotRequired[str]


class SendMailResponse(TypedDict):
    pass


class SendTemplatedEmailRequest(TypedDict):
    email: str
    expirationDateTime: str
    language: NotRequired[Optional[str]]
    messageId: str
    priority: Literal["HIGH", "LOW"]
    source: NotRequired[str]
    replyToAddresses: NotRequired[List[str]]
    attachments: NotRequired[List[Attachment]]
    account: NotRequired[str]
    templateName: str
    templateData: Dict[str, Any]


class SendTemplatedEmailResponse(TypedDict):
    pass


class EmailServiceEmailClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://email-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def send_mail(self, body: SendMailRequest):
        res = await self.client.request(
            path="/v1/private/sendEmail", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[SendMailResponse], res)

    async def send_templated_email(self, body: SendTemplatedEmailRequest):
        res = await self.client.request(
            path="/v1/private/sendTemplatedEmail", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[SendTemplatedEmailResponse], res)
