"""
Azure AI Search Hybrid Retriever
Purpose: Retrieve relevant documents using hybrid search
"""

from typing import List, Dict
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class HybridRetriever:
    """
    Retrieve documents using hybrid search (vector + keyword)

    WHY: Hybrid search combines:
         - Vector search: Semantic similarity (understands meaning)
         - Keyword search: Exact term matching (finds specific terms)
         - Best of both worlds: semantic understanding + precise matching
    """

    def __init__(self):
        """Initialize retriever components"""

        # Azure OpenAI client for query embeddings
        self.openai_client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint
        )

        # Azure AI Search client
        credential = AzureKeyCredential(settings.azure_search_admin_key)
        self.search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index_name,
            credential=credential
        )

        self.embedding_deployment = settings.azure_openai_embedding_deployment
        self.top_k = settings.top_k_results

        logger.info(f"HybridRetriever initialized")
        logger.info(f"  Top K results: {self.top_k}")

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for query"""
        response = self.openai_client.embeddings.create(
            input=query,
            model=self.embedding_deployment
        )
        return response.data[0].embedding

    def retrieve(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Retrieve relevant documents using hybrid search

        Args:
            query: User query string
            top_k: Number of results to return (default from settings)

        Returns:
            List of relevant documents with scores
        """
        if top_k is None:
            top_k = self.top_k

        logger.info(f"Retrieving documents for query: '{query}'")

        # Step 1: Generate query embedding
        query_embedding = self.embed_query(query)

        # Step 2: Create vector query
        # WHY: VectorizedQuery tells Azure Search to perform vector search
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,  # WHY: How many nearest neighbors to find
            fields="embedding"           # WHY: Which field contains vectors
        )

        # Step 3: Perform hybrid search
        # WHY: search_text + vector_queries = hybrid search
        #      Azure Search automatically combines scores using Reciprocal Rank Fusion (RRF)
        results = self.search_client.search(
            search_text=query,           # WHY: Keyword search component
            vector_queries=[vector_query], # WHY: Vector search component
            top=top_k,
            select=["id", "content", "source_file", "page", "chunk"]
        )

        # Step 4: Format results
        documents = []
        for result in results:
            doc = {
                "content": result["content"],
                "metadata": {
                    "source_file": result.get("source_file", ""),
                    "page": result.get("page", 0),
                    "chunk": result.get("chunk", 0),
                },
                "score": result.get("@search.score", 0.0)  # WHY: RRF combined score
            }
            documents.append(doc)

        logger.info(f"Retrieved {len(documents)} documents")

        return documents

    def format_context(self, documents: List[Dict]) -> str:
        """
        Format retrieved documents as context for LLM

        WHY: LLM needs context formatted clearly with source attribution
        """
        if not documents:
            return "No relevant documents found."

        context_parts = []

        for idx, doc in enumerate(documents, 1):
            source = doc["metadata"].get("source_file", "unknown")
            page = doc["metadata"].get("page", "?")
            score = doc.get("score", 0.0)

            context_parts.append(
                f"[Document {idx}] (Source: {source}, Page: {page}, Score: {score:.3f})\n"
                f"{doc['content']}\n"
            )

        return "\n".join(context_parts)


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    print("\n Testing Hybrid Retriever...")

    retriever = HybridRetriever()

    # Test queries
    test_queries = [
        "What is retrieval augmented generation?",
        "How does machine learning work?",
        "Explain embeddings and vector search"
    ]

    for query in test_queries:
        print(f"\n" + "="*80)
        print(f"Query: {query}")
        print("="*80)

        # Retrieve documents
        documents = retriever.retrieve(query, top_k=3)

        if not documents:
            print("No results found")
            continue

        # Display results
        for idx, doc in enumerate(documents, 1):
            print(f"\n[Result {idx}] Score: {doc['score']:.3f}")
            print(f"Source: {doc['metadata'].get('source_file')}, Page: {doc['metadata'].get('page')}")
            print(f"Content: {doc['content'][:200]}...")

        # Show formatted context
        print(f"\n--- Formatted Context ---")
        context = retriever.format_context(documents)
        print(context[:500] + "..." if len(context) > 500 else context)
