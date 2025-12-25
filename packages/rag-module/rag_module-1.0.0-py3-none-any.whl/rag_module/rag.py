"""Main RAG (Retrieval-Augmented Generation) implementation."""

from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from .chunker import TextChunker
from .document import Document
from .embeddings import OpenAIEmbeddings
from .loaders import MarkdownLoader, TextLoader
from .vector_store import VectorStore


@dataclass
class RAGResponse:
    """Response from a RAG query.

    Attributes:
        answer: The generated answer.
        sources: List of source documents used to generate the answer.
        scores: Similarity scores for each source document.
    """

    answer: str
    sources: list[Document]
    scores: list[float]


class RAG:
    """Retrieval-Augmented Generation engine.

    Combines document loading, chunking, embedding, vector storage,
    and LLM generation for question answering over documents.
    """

    def __init__(
        self,
        api_key: str | None = None,
        embedding_model: str = "text-embedding-3-small",
        chat_model: str = "gpt-4o-mini",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        """Initialize the RAG engine.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            embedding_model: Model for generating embeddings.
            chat_model: Model for generating answers.
            chunk_size: Size of text chunks in characters.
            chunk_overlap: Overlap between chunks in characters.
        """
        self.embeddings = OpenAIEmbeddings(api_key=api_key, model=embedding_model)
        self.vector_store = VectorStore()
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.text_loader = TextLoader()
        self.markdown_loader = MarkdownLoader()
        self.chat_model = chat_model
        self._client = OpenAI(api_key=api_key)

    def add_text(self, text: str, source: str = "string") -> int:
        """Add a text string to the knowledge base.

        Args:
            text: The text content to add.
            source: Optional source identifier.

        Returns:
            Number of chunks added.
        """
        doc = self.text_loader.load_from_string(text, source=source)
        chunks = self.chunker.chunk(doc)
        embeddings = self.embeddings.embed_documents(chunks)
        self.vector_store.add(chunks, embeddings)
        return len(chunks)

    def add_markdown(self, markdown: str, source: str = "string") -> int:
        """Add markdown content to the knowledge base.

        Args:
            markdown: The markdown content to add.
            source: Optional source identifier.

        Returns:
            Number of chunks added.
        """
        docs = self.markdown_loader.load_from_string(markdown, source=source)
        all_chunks: list[Document] = []
        for doc in docs:
            all_chunks.extend(self.chunker.chunk(doc))

        embeddings = self.embeddings.embed_documents(all_chunks)
        self.vector_store.add(all_chunks, embeddings)
        return len(all_chunks)

    def add_document(self, document: Document) -> int:
        """Add a document to the knowledge base.

        Args:
            document: The document to add.

        Returns:
            Number of chunks added.
        """
        chunks = self.chunker.chunk(document)
        embeddings = self.embeddings.embed_documents(chunks)
        self.vector_store.add(chunks, embeddings)
        return len(chunks)

    def add_documents(self, documents: list[Document]) -> int:
        """Add multiple documents to the knowledge base.

        Args:
            documents: List of documents to add.

        Returns:
            Total number of chunks added.
        """
        all_chunks = self.chunker.chunk_documents(documents)
        embeddings = self.embeddings.embed_documents(all_chunks)
        self.vector_store.add(all_chunks, embeddings)
        return len(all_chunks)

    def load_file(self, path: str | Path) -> int:
        """Load a file into the knowledge base.

        Automatically detects file type based on extension.

        Args:
            path: Path to the file.

        Returns:
            Number of chunks added.

        Raises:
            ValueError: If file type is not supported.
        """
        path = Path(path)
        suffix = path.suffix.lower()

        if suffix == ".md":
            docs = self.markdown_loader.load(path)
        elif suffix in (".txt", ".text"):
            docs = [self.text_loader.load(path)]
        else:
            # Try to load as plain text
            docs = [self.text_loader.load(path)]

        all_chunks: list[Document] = []
        for doc in docs:
            all_chunks.extend(self.chunker.chunk(doc))

        embeddings = self.embeddings.embed_documents(all_chunks)
        self.vector_store.add(all_chunks, embeddings)
        return len(all_chunks)

    def load_directory(
        self,
        path: str | Path,
        extensions: list[str] | None = None,
        recursive: bool = True,
    ) -> int:
        """Load all matching files from a directory.

        Args:
            path: Path to the directory.
            extensions: List of file extensions to include (e.g., [".md", ".txt"]).
                       If None, defaults to [".md", ".txt"].
            recursive: Whether to search subdirectories.

        Returns:
            Total number of chunks added.
        """
        path = Path(path)
        extensions = extensions or [".md", ".txt"]

        pattern = "**/*" if recursive else "*"
        total_chunks = 0

        for ext in extensions:
            for file_path in path.glob(f"{pattern}{ext}"):
                if file_path.is_file():
                    total_chunks += self.load_file(file_path)

        return total_chunks

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float | None = None,
    ) -> list[tuple[Document, float]]:
        """Search for relevant documents.

        Args:
            query: The search query.
            top_k: Maximum number of results.
            threshold: Optional minimum similarity threshold.

        Returns:
            List of (document, score) tuples.
        """
        query_embedding = self.embeddings.embed(query)
        return self.vector_store.search(query_embedding, top_k=top_k, threshold=threshold)

    def query(
        self,
        question: str,
        top_k: int = 5,
        system_prompt: str | None = None,
    ) -> RAGResponse:
        """Answer a question using RAG.

        Args:
            question: The question to answer.
            top_k: Number of context documents to retrieve.
            system_prompt: Optional custom system prompt.

        Returns:
            RAGResponse containing the answer and sources.
        """
        # Retrieve relevant documents
        results = self.search(question, top_k=top_k)

        if not results:
            return RAGResponse(
                answer="I don't have enough information to answer this question.",
                sources=[],
                scores=[],
            )

        sources = [doc for doc, _ in results]
        scores = [score for _, score in results]

        # Build context from retrieved documents
        context_parts: list[str] = []
        for i, (doc, score) in enumerate(results, 1):
            source_info = doc.metadata.get("source", "unknown")
            context_parts.append(f"[Source {i}: {source_info}]\n{doc.content}")

        context = "\n\n---\n\n".join(context_parts)

        # Generate answer
        default_system = (
            "You are a helpful assistant that answers questions based on the provided context. "
            "Use only the information from the context to answer. "
            "If the context doesn't contain enough information, say so. "
            "Cite sources by their number when using information from them."
        )

        messages = [
            {"role": "system", "content": system_prompt or default_system},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ]

        response = self._client.chat.completions.create(
            model=self.chat_model,
            messages=messages,  # type: ignore[arg-type]
        )

        answer = response.choices[0].message.content or ""

        return RAGResponse(answer=answer, sources=sources, scores=scores)

    def clear(self) -> None:
        """Clear all documents from the knowledge base."""
        self.vector_store.clear()

    @property
    def document_count(self) -> int:
        """Return the number of document chunks in the knowledge base."""
        return len(self.vector_store)
