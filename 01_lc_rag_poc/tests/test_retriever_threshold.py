"""
Test retrieval with score threshold
"""

from src.retriever import Retriever

def test_threshold_filtering():
    retriever = Retriever()

    query = "What is quantum computing?"  # Likely low relevance to our docs

    print(f"\nQuery: '{query}'")
    print("This query should have low relevance to our AI/ML documents\n")

    # Without threshold
    results_all = retriever.retrieve(query, k=5)
    print(f"Without threshold: {len(results_all)} results")

    # With high threshold
    results_filtered = retriever.retrieve_with_threshold(query, k=5, score_threshold=0.8)
    print(f"With threshold 0.8: {len(results_filtered)} results")

    if results_filtered:
        print("\nFiltered results:")
        for doc in results_filtered:
            print(f"  - {doc.metadata.get('source_file')}")
    else:
        print("\nNo results above threshold (expected for off-topic query)")

if __name__ == "__main__":
    test_threshold_filtering()
