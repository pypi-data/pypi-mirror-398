"""OpenAI embeddings integration."""

from openai import OpenAI

from .document import Document


class OpenAIEmbeddings:
    """Generate embeddings using OpenAI's embedding models."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-3-small",
    ) -> None:
        """Initialize the OpenAI embeddings client.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            model: The embedding model to use.
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text.

        Args:
            text: The text to embed.

        Returns:
            The embedding vector.
        """
        response = self.client.embeddings.create(
            input=text,
            model=self.model,
        )
        return response.data[0].embedding

    def embed_documents(self, documents: list[Document]) -> list[list[float]]:
        """Generate embeddings for multiple documents.

        Args:
            documents: List of documents to embed.

        Returns:
            List of embedding vectors, one per document.
        """
        if not documents:
            return []

        texts = [doc.content for doc in documents]
        return self.embed_batch(texts)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        response = self.client.embeddings.create(
            input=texts,
            model=self.model,
        )

        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]
