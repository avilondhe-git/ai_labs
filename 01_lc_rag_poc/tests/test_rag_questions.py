"""
Test RAG with different question types
"""

from src.rag_chain import RAGChain

def test_different_questions():
    rag = RAGChain()

    questions = {
        "Factual": "What is machine learning?",
        "List": "List the types of machine learning",
        "Comparison": "What's the difference between supervised and unsupervised learning?",
        "Off-topic": "What is the capital of France?",
    }

    for q_type, question in questions.items():
        print(f"\n{'='*60}")
        print(f"Type: {q_type}")
        print(f"Q: {question}")
        print(f"{'='*60}")

        result = rag.query(question, k=2)

        print(f"\nA: {result['answer'][:200]}...")
        print(f"\nSources: {result['num_sources']}")

if __name__ == "__main__":
    test_different_questions()
