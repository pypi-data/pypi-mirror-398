from typing import Union
from .conversation_message_content_part_text_param import (
    ConversationMessageContentPartTextParam,
)
from .conversation_message_content_part_image_param import (
    ConversationMessageContentPartImageParam,
)
from .conversation_message_content_part_input_audio_param import (
    ConversationMessageContentPartInputAudioParam,
)
from .conversation_message_content_part_pdf_param import (
    ConversationMessageContentPartPDFParam,
)

ConversationMessageContentPart = Union[
    ConversationMessageContentPartTextParam,
    ConversationMessageContentPartImageParam,
    ConversationMessageContentPartInputAudioParam,
    ConversationMessageContentPartPDFParam,
]


__all__ = ["ConversationMessageContentPart"]
