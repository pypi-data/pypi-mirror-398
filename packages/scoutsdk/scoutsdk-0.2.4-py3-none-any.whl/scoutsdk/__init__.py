"""Scout SDK - Python client library for Scout."""

from .api import ScoutAPI
from .api.project_helpers import scout
from scouttypes.assistants import AssistantFile
from scouttypes.conversations import SignedUploadUrlResponse
from scouttypes.constants import VariableNames, SCOUT_CUSTOM_FUNCTION_CONTENT_TYPE
from scouttypes.assistants import AssistantResponse
from scouttypes.document_chunker import (
    ChunkMetadata,
    Chunk,
    DocumentChunks,
    AbstractDocumentChunker,
)
from scouttypes.audio import AudioTranscriptionResponse
from scouttypes.protected import SignedUrlResponse

# Exposing CLI components
from .cli import ScoutCLI

from .crawlers.crawlers import crawlers, Crawler, CrawlerConfiguration
from .crawlers.indexers import indexers, Indexer

from .agents.scout_agent import ScoutAgent
from .agents.scout_agent_runner import ScoutAgentRunner

__all__ = [
    # API components
    "ScoutAPI",
    "AssistantResponse",
    "SCOUT_CUSTOM_FUNCTION_CONTENT_TYPE",
    # CLI components
    "ScoutCLI",
    # shared components
    "AssistantFile",
    "SignedUploadUrlResponse",
    "VariableNames",
    "scout",
    # Types
    "ChunkMetadata",
    "Chunk",
    "DocumentChunks",
    "AbstractDocumentChunker",
    "AudioTranscriptionResponse",
    "SignedUrlResponse",
    "indexers",
    "Indexer",
    "crawlers",
    "Crawler",
    "CrawlerConfiguration",
    "ScoutAgent",
    "ScoutAgentRunner",
    "FunctionProgress",
]
