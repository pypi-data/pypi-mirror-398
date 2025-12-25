"""Text chunking utilities for splitting documents."""

from .document import Document


class TextChunker:
    """Splits documents into smaller chunks for embedding.

    Uses a simple character-based splitting strategy with overlap
    to maintain context between chunks.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n",
    ) -> None:
        """Initialize the text chunker.

        Args:
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Number of overlapping characters between chunks.
            separator: Preferred separator for splitting text.

        Raises:
            ValueError: If chunk_overlap >= chunk_size.
        """
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def chunk(self, document: Document) -> list[Document]:
        """Split a document into smaller chunks.

        Args:
            document: The document to split.

        Returns:
            List of document chunks with inherited metadata.
        """
        text = document.content

        if len(text) <= self.chunk_size:
            return [document]

        # First try to split by separator
        splits = self._split_by_separator(text)

        # Then merge splits into appropriately sized chunks
        chunks = self._merge_splits(splits)

        # Create documents for each chunk
        documents: list[Document] = []
        for i, chunk_text in enumerate(chunks):
            chunk_doc = Document(
                content=chunk_text,
                metadata={
                    **document.metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            )
            documents.append(chunk_doc)

        return documents

    def chunk_documents(self, documents: list[Document]) -> list[Document]:
        """Split multiple documents into chunks.

        Args:
            documents: List of documents to split.

        Returns:
            Flattened list of all document chunks.
        """
        all_chunks: list[Document] = []
        for doc in documents:
            all_chunks.extend(self.chunk(doc))
        return all_chunks

    def _split_by_separator(self, text: str) -> list[str]:
        """Split text by the separator.

        Args:
            text: Text to split.

        Returns:
            List of text segments.
        """
        if self.separator:
            splits = text.split(self.separator)
        else:
            splits = [text]

        # Further split any segments that are still too large
        result: list[str] = []
        for split in splits:
            if len(split) <= self.chunk_size:
                result.append(split)
            else:
                # Fall back to sentence-like splitting
                result.extend(self._split_long_segment(split))

        return result

    def _split_long_segment(self, text: str) -> list[str]:
        """Split a long segment into smaller pieces.

        Tries to split on sentence boundaries first, then falls back
        to word boundaries, and finally character boundaries.

        Args:
            text: Long text segment to split.

        Returns:
            List of smaller text segments.
        """
        result: list[str] = []

        # Try splitting on sentence endings
        sentence_endings = [". ", "! ", "? ", ".\n", "!\n", "?\n"]
        current = text

        while len(current) > self.chunk_size:
            # Find a good split point
            split_point = self.chunk_size

            # Look for sentence ending
            for ending in sentence_endings:
                pos = current.rfind(ending, 0, self.chunk_size)
                if pos != -1:
                    split_point = pos + len(ending)
                    break
            else:
                # Fall back to space
                pos = current.rfind(" ", 0, self.chunk_size)
                if pos != -1:
                    split_point = pos + 1

            result.append(current[:split_point].strip())
            current = current[split_point:].strip()

        if current:
            result.append(current)

        return result

    def _merge_splits(self, splits: list[str]) -> list[str]:
        """Merge small splits into larger chunks with overlap.

        Args:
            splits: List of text segments.

        Returns:
            List of merged chunks.
        """
        if not splits:
            return []

        chunks: list[str] = []
        current_chunk: list[str] = []
        current_length = 0

        for split in splits:
            split = split.strip()
            if not split:
                continue

            split_length = len(split)

            # If adding this split would exceed chunk_size, save current and start new
            if current_length + split_length > self.chunk_size and current_chunk:
                chunks.append(self.separator.join(current_chunk))

                # Keep some content for overlap
                overlap_content: list[str] = []
                overlap_length = 0
                for item in reversed(current_chunk):
                    if overlap_length + len(item) <= self.chunk_overlap:
                        overlap_content.insert(0, item)
                        overlap_length += len(item)
                    else:
                        break

                current_chunk = overlap_content
                current_length = overlap_length

            current_chunk.append(split)
            current_length += split_length

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(self.separator.join(current_chunk))

        return chunks
