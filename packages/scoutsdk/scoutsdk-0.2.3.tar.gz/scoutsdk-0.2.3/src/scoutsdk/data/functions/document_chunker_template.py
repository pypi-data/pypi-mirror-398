from scoutsdk import scout, ScoutAPI
from scouttypes.document_chunker import (
    DocumentChunks,
    Chunk,
    ChunkMetadata,
    AbstractDocumentChunker,
)


@scout.document_chunker(
    priority=2
)  # Lower priority means that this chunker will be used first
class DemoChunker(AbstractDocumentChunker):
    def supports_document(
        self, url: str # https://, file:// ect...
    ) -> bool:  # Return true when your document chunker 
        # is able to process the url (might be file://)
        return True

    # Implement this method to take a document (URL or file path)
    # and break it into small, meaningful chunks suitable for embedding in a Retrieval-Augmented Generation (RAG) system.
    # Each chunk should represent a semantically coherent unit (e.g., paragraph or section)
    # to improve retrieval relevance and accuracy when the assistant answers user queries.
    def process_document(
        self, url: str
    ) -> DocumentChunks:  
        # Scout API can create basic chunks for you
        document_chunks = ScoutAPI().utils.chunk_document("path to file.ext")

        # Or create and add chunks
        return DocumentChunks(
            chunks=[
                Chunk(
                    chunk_to_embed="The content transformed into embeddings",
                    content_to_return="The content returned to the assistant when the embedding match the request.",
                    metadata=ChunkMetadata(
                        hierarchy=["heading 1", "heading 2"],
                        custom_property="Will be returned to the model",
                    ),
                )
            ]
        )
