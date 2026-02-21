"""
Vector Store Management
Purpose: Store and retrieve document embeddings using FAISS

CV Mapping: Vector databases, similarity search, embedding storage
"""

from typing import List, Optional, Any
from pathlib import Path
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

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class VectorStoreManager:
    """
    Manages vector database operations

    WHY: FAISS is chosen for:
         - Free and local (no cloud costs)
         - Python 3.10-3.14+ compatible
         - Fast similarity search (Facebook AI)
         - Easy to use with LangChain
    """

    def __init__(self, index_path: Optional[str] = None):
        """
        Initialize vector store manager

        Args:
            index_path: Where to store the FAISS index (default from config)
        """
        self.index_path = index_path or settings.vector_store_path
        self.collection_name = settings.collection_name

        # Ensure directory exists
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize embeddings
        # WHY: Same embedding model must be used for indexing and querying
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key
        )

        self.vectorstore = None

        logger.info(f"VectorStoreManager initialized")
        logger.info(f"  Index path: {self.index_path}")
        logger.info(f"  Collection: {self.collection_name}")

    def create_vectorstore(self, chunks: List[Document]) -> FAISS:
        """
        Create vector store from document chunks

        WHY: Batch creation is more efficient than incremental inserts

        Args:
            chunks: List of chunked documents

        Returns:
            FAISS vectorstore instance
        """
        logger.info(f"Creating FAISS vector store with {len(chunks)} chunks...")

        # STEP 1: Create embeddings and store
        # WHY: FAISS.from_documents handles embedding generation internally
        #      More efficient than manually generating embeddings first
        self.vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings
        )

        logger.info(f"Vector store created")
        logger.info(f"  Total vectors: {len(chunks)}")

        # STEP 2: Save to disk
        self.vectorstore.save_local(self.index_path)
        logger.info(f"  Index saved to: {self.index_path}")

        return self.vectorstore

    def load_vectorstore(self) -> Optional[FAISS]:
        """
        Load existing vector store from disk

        WHY: Avoids re-embedding documents on subsequent runs

        Returns:
            FAISS vectorstore instance or None if doesn't exist
        """
        index_file = Path(self.index_path) / "index.faiss"

        if not index_file.exists():
            logger.warning(f"FAISS index not found at {index_file}")
            return None

        try:
            self.vectorstore = FAISS.load_local(
                self.index_path,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True  # Required for pickle
            )

            # Get index info
            index_size = self.vectorstore.index.ntotal

            logger.info(f"Loaded existing FAISS index")
            logger.info(f"  Vectors in index: {index_size}")

            return self.vectorstore

        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            return None

    def similarity_search(self, query: str, k: int = None) -> List[Document]:
        """
        Search for similar documents

        WHY: Core retrieval function for RAG pipeline

        Args:
            query: Search query
            k: Number of results to return (default from config)

        Returns:
            List of most similar documents
        """
        if not self.vectorstore:
            raise ValueError("Vector store not initialized. Call create_vectorstore() or load_vectorstore() first")

        k = k or settings.top_k_results

        logger.info(f"Searching for: '{query}' (top {k} results)")

        # WHY: similarity_search uses cosine similarity by default
        #      Returns documents sorted by relevance score
        results = self.vectorstore.similarity_search(query, k=k)

        logger.info(f"Found {len(results)} results")

        return results

    def similarity_search_with_score(self, query: str, k: int = None) -> List[tuple]:
        """
        Search with relevance scores

        WHY: Scores help filter low-quality matches

        Returns:
            List of (Document, score) tuples
        """
        if not self.vectorstore:
            raise ValueError("Vector store not initialized")

        k = k or settings.top_k_results

        results = self.vectorstore.similarity_search_with_score(query, k=k)

        logger.info(f"Found {len(results)} results with scores")
        for i, (doc, score) in enumerate(results):
            logger.debug(f"  Result {i+1}: score={score:.4f}, source={doc.metadata.get('source_file')}")

        return results

    def delete_index(self):
        """Delete the FAISS index from disk"""
        import shutil
        index_path = Path(self.index_path)
        if index_path.exists():
            shutil.rmtree(index_path)
            logger.info(f"Deleted FAISS index: {index_path}")
            self.vectorstore = None
        else:
            logger.warning("No index to delete")


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    from src.document_loader import DocumentLoader
    from src.embedding_pipeline import EmbeddingPipeline

    print("\n📄 Step 1: Loading documents...")
    loader = DocumentLoader(data_dir="data/sample")
    documents = loader.load_documents()

    if not documents:
        print("No documents found")
        exit(1)

    print(f"Loaded {len(documents)} documents")

    print("\n✂️  Step 2: Chunking documents...")
    pipeline = EmbeddingPipeline()
    chunks = pipeline.chunk_documents(documents)
    print(f"Created {len(chunks)} chunks")

    print("\n🗄️  Step 3: Creating vector store...")
    print("⏳ Generating embeddings (this may take 10-30 seconds)...")

    vector_manager = VectorStoreManager()

    # Check if vector store already exists
    existing_store = vector_manager.load_vectorstore()

    if existing_store:
        print(f"Loaded existing FAISS index")
        user_input = input("\nIndex already exists. Recreate? (y/N): ")
        if user_input.lower() != 'y':
            print("Using existing index")
        else:
            print("Deleting old index...")
            vector_manager.delete_index()
            vectorstore = vector_manager.create_vectorstore(chunks)
    else:
        vectorstore = vector_manager.create_vectorstore(chunks)

    print(f"\nFAISS Vector Store Ready")

    # Test similarity search
    print("\nTesting similarity search...")
    test_queries = [
        "What is artificial intelligence?",
        "Explain machine learning types",
        "How does RAG work?"
    ]

    for query in test_queries:
        print(f"\n  Query: '{query}'")
        results = vector_manager.similarity_search(query, k=2)

        for i, doc in enumerate(results):
            source = doc.metadata.get('source_file', 'unknown')
            page = doc.metadata.get('page', 'N/A')
            preview = doc.page_content[:100].replace('\n', ' ')
            print(f"    Result {i+1}: [{source}, p.{page}] {preview}...")

    print(f"\nVector store is working correctly!")
    print(f"Index location: {vector_manager.index_path}")
