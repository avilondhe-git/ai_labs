"""
Retriever
Purpose: Retrieve relevant documents for a given query

CV Mapping: Information retrieval, semantic search, ranking algorithms
"""

from typing import List, Dict, Optional, Any
# from langchain.schema import Document
try:
    from langchain.schema import Document
except ImportError:
    try:
        from langchain_core.schema import Document
    except ImportError:
        try:
            from langchain.docstore.document import Document
        except ImportError:
            Document = Any
from src.vector_store import VectorStoreManager
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class Retriever:
    """
    Handles document retrieval from vector store

    WHY: Separate retriever enables:
         - Different retrieval strategies (semantic, hybrid, re-ranking)
         - Filtering and post-processing
         - Caching of frequent queries
    """

    def __init__(self, vector_manager: Optional[VectorStoreManager] = None):
        """
        Initialize retriever

        Args:
            vector_manager: Existing vector store manager (or create new)
        """
        # STEP 1: Load or create vector store
        if vector_manager:
            self.vector_manager = vector_manager
        else:
            self.vector_manager = VectorStoreManager()
            loaded = self.vector_manager.load_vectorstore()

            if not loaded:
                raise ValueError(
                    "No vector store found. Run src/vector_store.py first to create it."
                )

        logger.info("Retriever initialized")

    def retrieve(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Retrieve relevant documents for query

        WHY: Main retrieval interface - simple and clean

        Args:
            query: User question
            k: Number of documents to retrieve

        Returns:
            List of relevant documents
        """
        k = k or settings.top_k_results

        logger.info(f"Retrieving documents for query: '{query[:50]}...'")

        # STEP 1: Perform similarity search
        results = self.vector_manager.similarity_search(query, k=k)

        logger.info(f"Retrieved {len(results)} documents")

        return results

    def retrieve_with_scores(self, query: str, k: Optional[int] = None) -> List[tuple]:
        """
        Retrieve documents with relevance scores

        WHY: Scores enable filtering low-quality matches

        Returns:
            List of (Document, score) tuples
        """
        k = k or settings.top_k_results

        results = self.vector_manager.similarity_search_with_score(query, k=k)

        logger.info(f"Retrieved {len(results)} documents with scores")

        return results

    def retrieve_with_threshold(
        self,
        query: str,
        k: Optional[int] = None,
        score_threshold: float = 0.7
    ) -> List[Document]:
        """
        Retrieve documents above a relevance threshold

        WHY: Filters out low-quality matches to reduce LLM hallucinations

        Args:
            query: User question
            k: Max number of documents
            score_threshold: Minimum relevance score (0-1)

        Returns:
            List of documents above threshold
        """
        k = k or settings.top_k_results

        # Get results with scores
        results_with_scores = self.retrieve_with_scores(query, k=k)

        # Filter by threshold
        # WHY: FAISS returns distance (lower = more similar)
        #      Threshold filters documents above minimum relevance
        filtered_results = [
            doc for doc, score in results_with_scores
            if score >= score_threshold
        ]

        logger.info(
            f"Filtered to {len(filtered_results)}/{len(results_with_scores)} "
            f"documents above threshold {score_threshold}"
        )

        return filtered_results

    def format_retrieved_context(self, documents: List[Document]) -> str:
        """
        Format retrieved documents into context string for LLM

        WHY: LLMs need properly formatted context with source attribution

        Args:
            documents: Retrieved documents

        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant documents found."

        context_parts = []

        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source_file', 'unknown')
            page = doc.metadata.get('page', 'N/A')
            content = doc.page_content.strip()

            # Format: [Source 1: filename.pdf, page 3]
            # Content here...
            context_part = f"[Source {i}: {source}, page {page}]\n{content}"
            context_parts.append(context_part)

        # WHY: Separate sources with clear delimiters
        formatted_context = "\n\n---\n\n".join(context_parts)

        return formatted_context

    def get_retrieval_stats(self, documents: List[Document]) -> Dict:
        """Get statistics about retrieved documents"""
        if not documents:
            return {"count": 0}

        sources = {}
        for doc in documents:
            source = doc.metadata.get('source_file', 'unknown')
            sources[source] = sources.get(source, 0) + 1

        return {
            "count": len(documents),
            "sources": sources,
            "avg_length": sum(len(doc.page_content) for doc in documents) // len(documents)
        }


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    print("\nInitializing retriever...")

    try:
        retriever = Retriever()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease run: python src/vector_store.py")
        exit(1)

    print("Retriever ready\n")

    # Test queries
    test_queries = [
        "What is artificial intelligence?",
        "Explain the types of machine learning",
        "How does RAG reduce hallucinations?",
        "What are common ML evaluation metrics?"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        # Retrieve documents
        documents = retriever.retrieve(query, k=3)

        # Show stats
        stats = retriever.get_retrieval_stats(documents)
        print(f"\nRetrieved: {stats['count']} documents")
        print(f"Sources: {', '.join(stats['sources'].keys())}")
        print(f"Avg length: {stats['avg_length']} chars")

        # Show results
        print(f"\nResults:")
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source_file', 'unknown')
            page = doc.metadata.get('page', 'N/A')
            preview = doc.page_content[:150].replace('\n', ' ')
            print(f"\n  {i}. [{source}, p.{page}]")
            print(f"     {preview}...")

        # Show formatted context
        print(f"\n{'─'*60}")
        print("Formatted Context for LLM:")
        print(f"{'─'*60}")
        context = retriever.format_retrieved_context(documents)
        print(context[:500] + "..." if len(context) > 500 else context)

    print(f"\n{'='*60}")
    print("Retriever testing complete!")
