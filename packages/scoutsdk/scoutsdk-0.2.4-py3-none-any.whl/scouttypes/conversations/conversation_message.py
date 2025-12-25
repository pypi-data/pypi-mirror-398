from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict
from .message_role import MessageRole
from .message_metadata import MessageMetadata
from .message_tool_call import MessageToolCall
from .message_reasoning import MessageReasoning
from .stream_finish_reason import StreamFinishReason
from .conversation_message_content_part import ConversationMessageContentPart


class ConversationMessage(BaseModel):
    model_config = ConfigDict(extra="allow")
    role: MessageRole
    content: Optional[Union[str, List[ConversationMessageContentPart]]] = None
    tool_call_id: Optional[str] = None
    metadata: Optional[MessageMetadata] = None
    tool_calls: Optional[List[MessageToolCall]] = None
    reasoning: Optional[MessageReasoning] = None
    finish_reason: Optional[StreamFinishReason] = None


__all__ = ["ConversationMessage"]
