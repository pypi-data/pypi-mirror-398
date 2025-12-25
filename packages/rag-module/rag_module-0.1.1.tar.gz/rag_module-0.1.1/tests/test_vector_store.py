"""Tests for VectorStore class."""

import pytest

from rag_module import Document, VectorStore


class TestVectorStore:
    def test_empty_store(self) -> None:
        store = VectorStore()
        assert len(store) == 0

    def test_add_documents(self) -> None:
        store = VectorStore()
        docs = [
            Document(content="Hello", id="1"),
            Document(content="World", id="2"),
        ]
        embeddings = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]

        ids = store.add(docs, embeddings)

        assert len(store) == 2
        assert ids == ["1", "2"]
        assert "1" in store
        assert "2" in store

    def test_add_mismatched_raises_error(self) -> None:
        store = VectorStore()
        docs = [Document(content="Hello")]
        embeddings = [[1.0, 0.0], [0.0, 1.0]]

        with pytest.raises(ValueError, match="must match"):
            store.add(docs, embeddings)

    def test_search_empty_store(self) -> None:
        store = VectorStore()
        results = store.search([1.0, 0.0, 0.0])
        assert results == []

    def test_search_returns_similar(self) -> None:
        store = VectorStore()
        docs = [
            Document(content="A", id="a"),
            Document(content="B", id="b"),
            Document(content="C", id="c"),
        ]
        # Orthogonal vectors for clear similarity testing
        embeddings = [
            [1.0, 0.0, 0.0],  # A
            [0.0, 1.0, 0.0],  # B
            [0.7, 0.7, 0.0],  # C - similar to both A and B
        ]
        store.add(docs, embeddings)

        # Search for something similar to A
        results = store.search([1.0, 0.0, 0.0], top_k=2)

        assert len(results) == 2
        # First result should be A (exact match)
        assert results[0][0].id == "a"
        assert results[0][1] == pytest.approx(1.0)

    def test_search_with_threshold(self) -> None:
        store = VectorStore()
        docs = [
            Document(content="A", id="a"),
            Document(content="B", id="b"),
        ]
        embeddings = [[1.0, 0.0], [0.0, 1.0]]  # Orthogonal
        store.add(docs, embeddings)

        # With high threshold, orthogonal vectors shouldn't match
        results = store.search([1.0, 0.0], top_k=5, threshold=0.9)

        assert len(results) == 1
        assert results[0][0].id == "a"

    def test_delete(self) -> None:
        store = VectorStore()
        docs = [Document(content="A", id="1"), Document(content="B", id="2")]
        store.add(docs, [[1.0, 0.0], [0.0, 1.0]])

        deleted = store.delete(["1"])

        assert deleted == 1
        assert len(store) == 1
        assert "1" not in store
        assert "2" in store

    def test_delete_nonexistent(self) -> None:
        store = VectorStore()
        deleted = store.delete(["nonexistent"])
        assert deleted == 0

    def test_clear(self) -> None:
        store = VectorStore()
        docs = [Document(content="A"), Document(content="B")]
        store.add(docs, [[1.0], [0.0]])

        store.clear()

        assert len(store) == 0
