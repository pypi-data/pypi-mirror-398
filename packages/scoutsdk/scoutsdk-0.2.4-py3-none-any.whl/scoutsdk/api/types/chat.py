from pydantic import BaseModel
from typing import Any, Union, Literal, Optional


ImageContentTypes = Literal["image/png", "image/jpeg", "image/gif", "image/webp"]


class ChatCompletionMessageTextContent(BaseModel):
    text: str
    type: Literal["text"] = "text"


class ChatCompletionMessageImageContent(BaseModel):
    data: str  # base64 encoded image data
    content_type: ImageContentTypes
    filename: Optional[str] = None
    type: Literal["image"] = "image"


class ChatCompletionMessagePDFContent(BaseModel):
    data: str  # base64 encoded pdf data
    filename: Optional[str] = None
    type: Literal["pdf"] = "pdf"


class ChatCompletionMessage(BaseModel):
    role: str
    content: Union[
        str,
        list[
            ChatCompletionMessageTextContent
            | ChatCompletionMessageImageContent
            | ChatCompletionMessagePDFContent
            | dict[str, Any]
        ],
    ]
