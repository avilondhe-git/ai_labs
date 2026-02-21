"""
Azure AI Search Index Manager
Purpose: Create and manage search indexes with hybrid search
"""

from typing import List, Dict
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SimpleField,
    SearchableField
)
from azure.core.credentials import AzureKeyCredential
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class AzureSearchManager:
    """
    Manage Azure AI Search indexes

    WHY: Azure AI Search provides:
         - Hybrid search (vector + BM25 keyword)
         - Semantic ranking (L2 reranking)
         - Filters and facets
         - Enterprise scale and availability
    """

    def __init__(self):
        """Initialize Azure AI Search clients"""

        credential = AzureKeyCredential(settings.azure_search_admin_key)

        # WHY: SearchIndexClient creates/manages indexes
        self.index_client = SearchIndexClient(
            endpoint=settings.azure_search_endpoint,
            credential=credential
        )

        # WHY: SearchClient queries/uploads documents
        self.search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index_name,
            credential=credential
        )

        self.index_name = settings.azure_search_index_name

        logger.info(f"AzureSearchManager initialized")
        logger.info(f"  Endpoint: {settings.azure_search_endpoint}")
        logger.info(f"  Index: {self.index_name}")

    def create_index(self):
        """
        Create search index with hybrid search configuration

        WHY: This schema enables:
             - Vector search with HNSW algorithm (fast approximate nearest neighbor)
             - Keyword search on content
             - Filters on metadata fields
        """

        # WHY: Vector search configuration for HNSW algorithm
        #      HNSW = Hierarchical Navigable Small World (fast vector search)
        vector_search = VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="vector-profile",
                    algorithm_configuration_name="hnsw-config"
                )
            ],
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-config",
                    parameters={
                        "m": 4,              # WHY: Connections per layer (balance speed/accuracy)
                        "efConstruction": 400, # WHY: Build quality (higher = better but slower)
                        "efSearch": 500,      # WHY: Search quality (higher = better but slower)
                        "metric": "cosine"    # WHY: Similarity metric for embeddings
                    }
                )
            ]
        )

        # WHY: Define index fields
        fields = [
            # Unique document ID
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True
            ),

            # Document content (searchable with keyword search)
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                analyzer_name="en.microsoft"  # WHY: Language-aware tokenization
            ),

            # Vector embedding (searchable with vector search)
            SearchField(
                name="embedding",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                vector_search_dimensions=1536,  # WHY: ada-002 embedding size
                vector_search_profile_name="vector-profile"
            ),

            # Metadata fields (filterable for faceted search)
            SimpleField(name="source_file", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="page", type=SearchFieldDataType.Int32, filterable=True),
            SimpleField(name="chunk", type=SearchFieldDataType.Int32, filterable=True)
        ]

        # Create index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )

        try:
            # Check if index exists
            try:
                self.index_client.get_index(self.index_name)
                logger.warning(f"Index '{self.index_name}' already exists - deleting...")
                self.index_client.delete_index(self.index_name)
            except:
                pass

            # Create new index
            self.index_client.create_index(index)
            logger.info(f"Created index: {self.index_name}")

        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            raise

    def upload_documents(self, documents: List[Dict]):
        """
        Upload documents to search index

        Args:
            documents: List of dicts with page_content, embedding, and metadata
        """

        # WHY: Convert to Azure Search document format
        search_documents = []
        for idx, doc in enumerate(documents):
            search_doc = {
                "id": f"doc_{idx}",  # WHY: Unique ID required by Azure Search
                "content": doc["page_content"],
                "embedding": doc["embedding"],
                "source_file": doc["metadata"].get("source_file", ""),
                "page": doc["metadata"].get("page", 0),
                "chunk": doc["metadata"].get("chunk", 0)
            }
            search_documents.append(search_doc)

        # WHY: Upload in batches (Azure Search limit: 1000 docs per batch)
        batch_size = 100
        total_batches = (len(search_documents) + batch_size - 1) // batch_size

        logger.info(f"Uploading {len(search_documents)} documents in {total_batches} batches...")

        for i in range(0, len(search_documents), batch_size):
            batch = search_documents[i:i + batch_size]

            try:
                result = self.search_client.upload_documents(documents=batch)
                logger.info(f"  Batch {i//batch_size + 1}/{total_batches} complete")

            except Exception as e:
                logger.error(f"Batch {i//batch_size + 1} failed: {e}")
                continue

        logger.info(f"Uploaded {len(search_documents)} documents")

    def get_index_stats(self) -> Dict:
        """Get index statistics"""
        try:
            stats = self.search_client.get_document_count()
            return {"document_count": stats}
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    from src.azure_blob_loader import AzureBlobDocumentLoader
    from src.embedding_pipeline import EmbeddingPipeline

    print("\n Loading and embedding documents...")

    # Load documents
    loader = AzureBlobDocumentLoader()
    documents = loader.load_documents()

    if not documents:
        print("No documents found")
        exit(1)

    # Generate embeddings
    pipeline = EmbeddingPipeline()
    embedded_docs = pipeline.process_documents(documents)

    print(f"Prepared {len(embedded_docs)} embedded documents")

    # Create search index
    print("\n Creating Azure AI Search index...")
    manager = AzureSearchManager()

    # Create index
    manager.create_index()

    # Upload documents
    print("\n Uploading documents to search index...")
    manager.upload_documents(embedded_docs)

    # Get stats
    stats = manager.get_index_stats()

    print(f"\n Index Creation Complete")
    print(f"  Index name: {manager.index_name}")
    print(f"  Documents indexed: {stats.get('document_count', 0)}")
    print(f"  Features enabled:")
    print(f"    - Vector search (HNSW algorithm)")
    print(f"    - Keyword search (BM25)")
    print(f"    - Hybrid search (vector + keyword)")
    print(f"    - Metadata filters")
