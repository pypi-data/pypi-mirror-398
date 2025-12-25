"""Document data structure for RAG module."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """Represents a document or chunk of text with metadata.

    Attributes:
        content: The text content of the document.
        metadata: Optional metadata associated with the document.
        id: Optional unique identifier for the document.
    """

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str | None = None

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("Document content cannot be empty")

    def __repr__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Document(id={self.id}, content='{preview}')"
