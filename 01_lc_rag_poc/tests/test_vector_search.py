"""
Test vector search with scores
"""

from src.vector_store import VectorStoreManager

def test_search_with_scores():
    manager = VectorStoreManager()
    manager.load_vectorstore()

    query = "What is machine learning?"
    results = manager.similarity_search_with_score(query, k=3)

    print(f"\nQuery: '{query}'\n")
    for i, (doc, score) in enumerate(results):
        print(f"Result {i+1}:")
        print(f"  Score: {score:.4f}")
        print(f"  Source: {doc.metadata.get('source_file')}")
        print(f"  Page: {doc.metadata.get('page')}")
        print(f"  Content: {doc.page_content[:150]}...\n")

if __name__ == "__main__":
    test_search_with_scores()
