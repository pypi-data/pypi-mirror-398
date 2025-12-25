"""Demo script showing how to use the RAG module with sample documents."""

from pathlib import Path

from rag_module import RAG

# Initialize RAG (uses OPENAI_API_KEY env var by default)
rag = RAG()

# Load the sample documents
examples_dir = Path(__file__).parent
rag.load_file(examples_dir / "genetic_engineering.md")
rag.load_file(examples_dir / "finance.md")

print(f"Loaded {rag.document_count} chunks into the knowledge base\n")

# Example queries
queries = [
    "What is CRISPR and who discovered it?",
    "Explain the time value of money",
    "What are the ethical concerns around genetic engineering?",
    "What is the 50/30/20 budgeting rule?",
    "How is genetic engineering used in medicine?",
]

for query in queries:
    print(f"Q: {query}")
    response = rag.query(query, top_k=3)
    print(f"A: {response.answer}\n")
    print("-" * 60 + "\n")
