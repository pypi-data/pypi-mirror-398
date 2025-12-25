"""Basic example showing how to use the RAG module."""

from rag_module import RAG
from dotenv import load_dotenv

load_dotenv()

# Initialize (uses OPENAI_API_KEY env var)
rag = RAG()

# Add documents
rag.add_text("Python is a programming language created by Guido van Rossum.")
rag.add_markdown("# Machine Learning\n\nML is a subset of artificial intelligence.")

# Query
response = rag.query("What is Python?")

# Print answer
print("Answer:", response.answer)

# Print sources cleanly
if response.sources:
    print("\nSources:")
    for i, (doc, score) in enumerate(zip(response.sources, response.scores), 1):
        source = doc.metadata.get("source", "unknown")
        preview = doc.content[:100].replace("\n", " ")
        if len(doc.content) > 100:
            preview += "..."
        print(f"  [{i}] (score: {score:.3f}) {source}")
        print(f"      {preview}")
