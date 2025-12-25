"""Document loaders for text and markdown files."""

import re
from pathlib import Path

from .document import Document


class TextLoader:
    """Loader for plain text files."""

    def load(self, path: str | Path) -> Document:
        """Load a text file as a document.

        Args:
            path: Path to the text file.

        Returns:
            Document containing the file contents.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is empty.
        """
        path = Path(path)
        content = path.read_text(encoding="utf-8")

        if not content.strip():
            raise ValueError(f"File is empty: {path}")

        return Document(
            content=content,
            metadata={
                "source": str(path),
                "filename": path.name,
                "type": "text",
            },
        )

    def load_from_string(self, content: str, source: str = "string") -> Document:
        """Create a document from a string.

        Args:
            content: The text content.
            source: Optional source identifier.

        Returns:
            Document containing the content.
        """
        return Document(
            content=content,
            metadata={
                "source": source,
                "type": "text",
            },
        )


class MarkdownLoader:
    """Loader for markdown files with optional section parsing."""

    def __init__(self, split_by_headers: bool = False) -> None:
        """Initialize the markdown loader.

        Args:
            split_by_headers: If True, split document into sections by headers.
        """
        self.split_by_headers = split_by_headers

    def load(self, path: str | Path) -> list[Document]:
        """Load a markdown file as document(s).

        Args:
            path: Path to the markdown file.

        Returns:
            List of documents. If split_by_headers is True, returns one document
            per section; otherwise returns a single document.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is empty.
        """
        path = Path(path)
        content = path.read_text(encoding="utf-8")

        if not content.strip():
            raise ValueError(f"File is empty: {path}")

        base_metadata = {
            "source": str(path),
            "filename": path.name,
            "type": "markdown",
        }

        if not self.split_by_headers:
            return [Document(content=content, metadata=base_metadata)]

        return self._split_by_headers(content, base_metadata)

    def load_from_string(
        self,
        content: str,
        source: str = "string",
    ) -> list[Document]:
        """Create document(s) from a markdown string.

        Args:
            content: The markdown content.
            source: Optional source identifier.

        Returns:
            List of documents.
        """
        base_metadata = {
            "source": source,
            "type": "markdown",
        }

        if not self.split_by_headers:
            return [Document(content=content, metadata=base_metadata)]

        return self._split_by_headers(content, base_metadata)

    def _split_by_headers(
        self,
        content: str,
        base_metadata: dict[str, str],
    ) -> list[Document]:
        """Split markdown content by headers.

        Args:
            content: The markdown content.
            base_metadata: Base metadata to include in each document.

        Returns:
            List of documents, one per section.
        """
        header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        matches = list(header_pattern.finditer(content))

        if not matches:
            return [Document(content=content, metadata=base_metadata)]

        documents: list[Document] = []

        # Content before first header
        if matches[0].start() > 0:
            preamble = content[: matches[0].start()].strip()
            if preamble:
                documents.append(
                    Document(
                        content=preamble,
                        metadata={**base_metadata, "section": "preamble"},
                    )
                )

        # Process each section
        for i, match in enumerate(matches):
            header_level = len(match.group(1))
            header_text = match.group(2).strip()

            # Get section content
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section_content = content[start:end].strip()

            if section_content:
                documents.append(
                    Document(
                        content=section_content,
                        metadata={
                            **base_metadata,
                            "section": header_text,
                            "header_level": header_level,
                        },
                    )
                )

        return documents
