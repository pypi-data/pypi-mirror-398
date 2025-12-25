"""In-memory vector store implementation."""

import uuid
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .document import Document


@dataclass
class VectorEntry:
    """An entry in the vector store containing a document and its embedding."""

    id: str
    document: Document
    embedding: NDArray[np.float32]


class VectorStore:
    """In-memory vector store using cosine similarity for retrieval.

    This vector store keeps all documents and embeddings in memory,
    using numpy for efficient similarity calculations.
    """

    def __init__(self) -> None:
        """Initialize an empty vector store."""
        self._entries: dict[str, VectorEntry] = {}

    def add(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
    ) -> list[str]:
        """Add documents with their embeddings to the store.

        Args:
            documents: List of documents to add.
            embeddings: List of embedding vectors corresponding to each document.

        Returns:
            List of IDs assigned to the added documents.

        Raises:
            ValueError: If the number of documents doesn't match the number of embeddings.
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Number of documents ({len(documents)}) must match "
                f"number of embeddings ({len(embeddings)})"
            )

        ids: list[str] = []
        for doc, embedding in zip(documents, embeddings):
            doc_id = doc.id or str(uuid.uuid4())
            entry = VectorEntry(
                id=doc_id,
                document=doc,
                embedding=np.array(embedding, dtype=np.float32),
            )
            self._entries[doc_id] = entry
            ids.append(doc_id)

        return ids

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        threshold: float | None = None,
    ) -> list[tuple[Document, float]]:
        """Search for similar documents using cosine similarity.

        Args:
            query_embedding: The embedding vector of the query.
            top_k: Maximum number of results to return.
            threshold: Optional minimum similarity threshold (0-1).

        Returns:
            List of (document, similarity_score) tuples, sorted by similarity descending.
        """
        if not self._entries:
            return []

        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)

        if query_norm == 0:
            return []

        query_vec = query_vec / query_norm

        results: list[tuple[Document, float]] = []

        for entry in self._entries.values():
            entry_norm = np.linalg.norm(entry.embedding)
            if entry_norm == 0:
                continue

            normalized_embedding = entry.embedding / entry_norm
            similarity = float(np.dot(query_vec, normalized_embedding))

            if threshold is None or similarity >= threshold:
                results.append((entry.document, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def delete(self, ids: list[str]) -> int:
        """Delete documents by their IDs.

        Args:
            ids: List of document IDs to delete.

        Returns:
            Number of documents actually deleted.
        """
        deleted = 0
        for doc_id in ids:
            if doc_id in self._entries:
                del self._entries[doc_id]
                deleted += 1
        return deleted

    def clear(self) -> None:
        """Remove all documents from the store."""
        self._entries.clear()

    def __len__(self) -> int:
        """Return the number of documents in the store."""
        return len(self._entries)

    def __contains__(self, doc_id: str) -> bool:
        """Check if a document ID exists in the store."""
        return doc_id in self._entries
