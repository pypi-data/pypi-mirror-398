# RAG Module

A simple RAG (Retrieval-Augmented Generation) module with an in-memory vector store and OpenAI integration.

## Installation

```bash
pip install rag-module
```

## Requirements

- Python 3.12+
- OpenAI API key

## Quick Start

```python
from rag_module import RAG

# Initialize with your OpenAI API key
rag = RAG(api_key="your-api-key")

# Add documents
rag.add_text("Python is a programming language created by Guido van Rossum.")
rag.add_markdown("# Machine Learning\n\nML is a subset of artificial intelligence.")

# Load files
rag.load_file("docs/guide.md")
rag.load_directory("docs/", extensions=[".md", ".txt"])

# Query
response = rag.query("What is Python?")
print(response.answer)
print(response.sources)
```

## Components

### RAG

The main class that orchestrates document loading, embedding, and querying.

```python
from rag_module import RAG

rag = RAG(
    api_key="your-api-key",           # Or set OPENAI_API_KEY env var
    embedding_model="text-embedding-3-small",
    chat_model="gpt-4o-mini",
    chunk_size=1000,
    chunk_overlap=200,
)
```

### Document

Represents a piece of text with metadata.

```python
from rag_module import Document

doc = Document(
    content="Hello world",
    metadata={"source": "example.txt"},
    id="doc-1"
)
```

### VectorStore

In-memory vector store using cosine similarity.

```python
from rag_module import VectorStore

store = VectorStore()
store.add(documents, embeddings)
results = store.search(query_embedding, top_k=5)
```

### TextChunker

Splits documents into smaller chunks.

```python
from rag_module import TextChunker

chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
chunks = chunker.chunk(document)
```

### Loaders

Load documents from files or strings.

```python
from rag_module import TextLoader, MarkdownLoader

# Text files
loader = TextLoader()
doc = loader.load("file.txt")
doc = loader.load_from_string("content", source="inline")

# Markdown files
md_loader = MarkdownLoader(split_by_headers=True)
docs = md_loader.load("file.md")
```

### OpenAIEmbeddings

Generate embeddings using OpenAI.

```python
from rag_module import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector = embeddings.embed("Hello world")
vectors = embeddings.embed_batch(["Hello", "World"])
```

## Development

```bash
# Install dev dependencies
make install-dev

# Run tests
make test

# Format code
make format

# Type check
make typecheck

# Build package
make build
```

## License

MIT
