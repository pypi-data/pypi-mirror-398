"""Tests for TextChunker class."""

import pytest

from rag_module import Document, TextChunker


class TestTextChunker:
    def test_invalid_overlap_raises_error(self) -> None:
        with pytest.raises(ValueError, match="must be less than"):
            TextChunker(chunk_size=100, chunk_overlap=100)

    def test_small_document_no_chunking(self) -> None:
        chunker = TextChunker(chunk_size=1000)
        doc = Document(content="Short text")

        chunks = chunker.chunk(doc)

        assert len(chunks) == 1
        assert chunks[0].content == "Short text"

    def test_large_document_chunking(self) -> None:
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph here."
        doc = Document(content=content, metadata={"source": "test"})

        chunks = chunker.chunk(doc)

        assert len(chunks) > 1
        # All chunks should have original metadata plus chunk info
        for chunk in chunks:
            assert chunk.metadata["source"] == "test"
            assert "chunk_index" in chunk.metadata
            assert "total_chunks" in chunk.metadata

    def test_chunk_documents(self) -> None:
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        docs = [
            Document(content="Short"),
            Document(content="A longer document that needs to be chunked into pieces."),
        ]

        chunks = chunker.chunk_documents(docs)

        assert len(chunks) >= 2  # At least one chunk from each doc

    def test_chunk_preserves_metadata(self) -> None:
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        doc = Document(
            content="A" * 100,
            metadata={"source": "test.txt", "author": "John"},
        )

        chunks = chunker.chunk(doc)

        for chunk in chunks:
            assert chunk.metadata["source"] == "test.txt"
            assert chunk.metadata["author"] == "John"
