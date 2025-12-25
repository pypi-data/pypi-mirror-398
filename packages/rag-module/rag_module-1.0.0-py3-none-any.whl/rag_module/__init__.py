"""RAG Module - A simple RAG implementation with in-memory vector store and OpenAI integration."""

from .chunker import TextChunker
from .document import Document
from .embeddings import OpenAIEmbeddings
from .loaders import MarkdownLoader, TextLoader
from .rag import RAG
from .vector_store import VectorStore

__version__ = "1.0.0"

__all__ = [
    "RAG",
    "VectorStore",
    "Document",
    "TextChunker",
    "OpenAIEmbeddings",
    "TextLoader",
    "MarkdownLoader",
]
