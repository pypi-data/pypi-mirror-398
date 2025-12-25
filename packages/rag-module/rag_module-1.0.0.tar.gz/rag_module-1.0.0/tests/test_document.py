"""Tests for Document class."""

import pytest

from rag_module import Document


class TestDocument:
    def test_create_document(self) -> None:
        doc = Document(content="Hello world")
        assert doc.content == "Hello world"
        assert doc.metadata == {}
        assert doc.id is None

    def test_create_document_with_metadata(self) -> None:
        doc = Document(
            content="Hello world",
            metadata={"source": "test.txt"},
            id="doc-1",
        )
        assert doc.content == "Hello world"
        assert doc.metadata == {"source": "test.txt"}
        assert doc.id == "doc-1"

    def test_empty_content_raises_error(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            Document(content="")

    def test_repr(self) -> None:
        doc = Document(content="Hello world", id="doc-1")
        assert "doc-1" in repr(doc)
        assert "Hello world" in repr(doc)

    def test_repr_truncates_long_content(self) -> None:
        long_content = "x" * 100
        doc = Document(content=long_content)
        assert "..." in repr(doc)
