"""Tests for document loaders."""

from pathlib import Path

import pytest

from rag_module import MarkdownLoader, TextLoader


class TestTextLoader:
    def test_load_from_string(self) -> None:
        loader = TextLoader()
        doc = loader.load_from_string("Hello world", source="inline")

        assert doc.content == "Hello world"
        assert doc.metadata["source"] == "inline"
        assert doc.metadata["type"] == "text"

    def test_load_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.txt"
        file_path.write_text("File content here")

        loader = TextLoader()
        doc = loader.load(file_path)

        assert doc.content == "File content here"
        assert doc.metadata["filename"] == "test.txt"
        assert doc.metadata["type"] == "text"

    def test_load_empty_file_raises_error(self, tmp_path: Path) -> None:
        file_path = tmp_path / "empty.txt"
        file_path.write_text("   ")  # Whitespace only

        loader = TextLoader()
        with pytest.raises(ValueError, match="empty"):
            loader.load(file_path)

    def test_load_nonexistent_file_raises_error(self) -> None:
        loader = TextLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/file.txt")


class TestMarkdownLoader:
    def test_load_from_string(self) -> None:
        loader = MarkdownLoader()
        docs = loader.load_from_string("# Title\n\nContent here")

        assert len(docs) == 1
        assert "# Title" in docs[0].content
        assert docs[0].metadata["type"] == "markdown"

    def test_load_split_by_headers(self) -> None:
        loader = MarkdownLoader(split_by_headers=True)
        content = """Preamble text

# Header 1

Content for section 1

## Header 2

Content for section 2
"""
        docs = loader.load_from_string(content)

        # Should have: preamble, header 1, header 2
        assert len(docs) == 3
        assert docs[0].metadata.get("section") == "preamble"
        assert docs[1].metadata.get("section") == "Header 1"
        assert docs[2].metadata.get("section") == "Header 2"
        assert docs[2].metadata.get("header_level") == 2

    def test_load_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("# Markdown\n\nContent")

        loader = MarkdownLoader()
        docs = loader.load(file_path)

        assert len(docs) == 1
        assert docs[0].metadata["filename"] == "test.md"
        assert docs[0].metadata["type"] == "markdown"

    def test_load_empty_file_raises_error(self, tmp_path: Path) -> None:
        file_path = tmp_path / "empty.md"
        file_path.write_text("")

        loader = MarkdownLoader()
        with pytest.raises(ValueError, match="empty"):
            loader.load(file_path)

    def test_no_headers_returns_single_doc(self) -> None:
        loader = MarkdownLoader(split_by_headers=True)
        docs = loader.load_from_string("Just plain text without headers")

        assert len(docs) == 1
