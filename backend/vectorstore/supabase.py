import time
from typing import Any, List

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores import SupabaseVectorStore
from logger import get_logger
from supabase.client import Client

logger = get_logger(__name__)


class CustomSupabaseVectorStore(SupabaseVectorStore):
    """A custom vector store that uses the match_vectors table instead of the vectors table."""

    brain_id: str = "none"
    user_id: str = "none"
    number_docs: int = 35
    max_input: int = 2000

    def __init__(
        self,
        client: Client,
        embedding: Embeddings,
        table_name: str,
        brain_id: str = "none",
        user_id: str = "none",
        number_docs: int = 35,
        max_input: int = 2000,
    ):
        super().__init__(client, embedding, table_name)
        self.brain_id = brain_id
        self.user_id = user_id
        self.number_docs = number_docs
        self.max_input = max_input

    def find_brain_closest_query(
        self,
        user_id: str,
        query: str,
        k: int = 6,
        table: str = "match_brain",
        threshold: float = 0.5,
    ) -> [dict]:
        vectors = self._embed_query_with_retry(query)
        query_embedding = vectors[0]

        res = self._client.rpc(
            table,
            {
                "query_embedding": query_embedding,
                "match_count": self.number_docs,
                "p_user_id": str(self.user_id),
            },
        ).execute()

        # Get the brain_id of the brain that is most similar to the query
        # Get the brain_id and name of the brains that are most similar to the query
        brain_details = [
            {
                "id": item.get("id", None),
                "name": item.get("name", None),
                "similarity": item.get("similarity", 0.0),
            }
            for item in res.data
        ]
        return brain_details

    def similarity_search(
        self,
        query: str,
        k: int = 40,
        table: str = "match_vectors",
        threshold: float = 0.5,
        **kwargs: Any,
    ) -> List[Document]:
        vectors = self._embed_query_with_retry(query)
        query_embedding = vectors[0]
        res = self._client.rpc(
            table,
            {
                "query_embedding": query_embedding,
                "max_chunk_sum": self.max_input,
                "p_brain_id": str(self.brain_id),
            },
        ).execute()

        match_result = [
            Document(
                metadata={
                    **search.get("metadata", {}),
                    "id": search.get("id", ""),
                    "similarity": search.get("similarity", 0.0),
                },
                page_content=search.get("content", ""),
            )
            for search in res.data
            if search.get("content")
        ]

        # The database function uses the chunk_size saved at ingestion time.
        # For some extracted PDFs that metadata is smaller than the actual
        # returned text, so a nominal 7k-character budget could otherwise
        # send tens of thousands of characters to the local LLM.  That slows
        # CPU inference and makes the answer model focus on unrelated chunks.
        # Keep the highest-similarity passages and enforce the real text
        # budget here as the final retrieval safeguard.
        match_result.sort(
            key=lambda document: document.metadata.get("similarity", 0.0),
            reverse=True,
        )
        selected_documents: List[Document] = []
        used_characters = 0
        for document in match_result:
            document_length = len(document.page_content)
            if used_characters + document_length <= self.max_input:
                selected_documents.append(document)
                used_characters += document_length
            elif not selected_documents:
                # Always return the best match, even when a single extracted
                # PDF chunk is larger than the configured context budget.
                document.page_content = document.page_content[: self.max_input]
                selected_documents.append(document)
                break

        return selected_documents

    def _embed_query_with_retry(self, query: str) -> List[List[float]]:
        """Absorb brief Ollama startup/network interruptions before failing a query."""
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                return self._embedding.embed_documents([query])
            except Exception as error:
                last_error = error
                if attempt < 2:
                    logger.warning(
                        "Embedding request failed (attempt %s/3); retrying: %s",
                        attempt + 1,
                        error,
                    )
                    time.sleep(attempt + 1)
        raise RuntimeError("Local embedding service is unavailable") from last_error
