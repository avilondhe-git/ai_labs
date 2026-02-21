"""
Embedding Pipeline
Purpose: Chunk documents and generate embeddings

CV Mapping: Text preprocessing, embedding generation, vector representations
"""

from typing import List, Any
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# text‑splitter moved around between releases
# from langchain.schema import Document
# text‑splitter has wandered around a bit
try:
    from langchain.text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
        except ImportError:
            RecursiveCharacterTextSplitter = None   # type: ignore

if RecursiveCharacterTextSplitter is None:
    raise ImportError(
        "RecursiveCharacterTextSplitter cannot be imported. "
        "Install langchain-text-splitters (e.g. "
        "`pip install langchain-text-splitters==1.1.1`) or pin a "
        "compatible LangChain release in requirements.txt."
    )

# document type location varies as well
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

from langchain_openai import OpenAIEmbeddings
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class EmbeddingPipeline:
    """
    Handles document chunking and embedding generation

    WHY: Separating chunking from embedding allows independent optimization
         Can experiment with chunk sizes without re-generating embeddings
    """

    def __init__(self):
        """Initialize embedding pipeline"""
        # WHY: Validate API key before proceeding
        settings.validate_api_key()

        # STEP 1: Initialize text splitter
        # WHY: RecursiveCharacterTextSplitter preserves semantic boundaries
        #      Tries to split on paragraphs, then sentences, then words
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,           # WHY: 1000 tokens balances context vs specificity
            chunk_overlap=settings.chunk_overlap,     # WHY: 200 token overlap prevents context loss
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # WHY: Prioritize semantic boundaries
        )

        # STEP 2: Initialize embeddings model
        # WHY: text-embedding-3-small is cost-effective and performant
        #      Cost: $0.02/1M tokens (10x cheaper than text-embedding-ada-002)
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key
        )

        logger.info(f"EmbeddingPipeline initialized")
        logger.info(f"  Chunk size: {settings.chunk_size}")
        logger.info(f"  Chunk overlap: {settings.chunk_overlap}")
        logger.info(f"  Embedding model: {settings.embedding_model}")

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks

        WHY: LLMs have context limits; smaller chunks improve retrieval precision

        Args:
            documents: List of Document objects

        Returns:
            List of chunked Document objects
        """
        logger.info(f"Chunking {len(documents)} documents...")

        # STEP 1: Split documents
        chunks = self.text_splitter.split_documents(documents)

        # STEP 2: Enrich chunk metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata['chunk_id'] = i
            # WHY: Chunk ID enables tracking which chunks were retrieved

        logger.info(f"Created {len(chunks)} chunks")
        logger.info(f"  Average chunk size: {sum(len(c.page_content) for c in chunks) // len(chunks)} chars")

        return chunks

    def get_chunk_stats(self, chunks: List[Document]) -> dict:
        """Get statistics about chunks"""
        if not chunks:
            return {}

        chunk_sizes = [len(chunk.page_content) for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "min_size": min(chunk_sizes),
            "max_size": max(chunk_sizes),
            "avg_size": sum(chunk_sizes) // len(chunks),
            "total_chars": sum(chunk_sizes)
        }

    def test_embedding_generation(self, sample_text: str = "This is a test.") -> bool:
        """
        Test that embeddings can be generated

        WHY: Fail fast if API key is invalid

        Returns:
            True if successful, False otherwise
        """
        try:
            embedding = self.embeddings.embed_query(sample_text)
            logger.info(f"Embedding test successful")
            logger.info(f"  Embedding dimension: {len(embedding)}")
            return True
        except Exception as e:
            logger.error(f"Embedding test failed: {e}")
            return False


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    from src.document_loader import DocumentLoader

    print("\n📄 Step 1: Loading documents...")
    loader = DocumentLoader(data_dir="data/sample")
    documents = loader.load_documents()

    if not documents:
        print("No documents found. Run tests/generate_test_data.py first")
        exit(1)

    print(f"Loaded {len(documents)} documents")

    print("\n🔧 Step 2: Initializing embedding pipeline...")
    pipeline = EmbeddingPipeline()

    print("\n🧪 Step 3: Testing embedding generation...")
    if not pipeline.test_embedding_generation():
        print("Embedding generation failed. Check your OPENAI_API_KEY in .env")
        exit(1)

    print("\n✂️  Step 4: Chunking documents...")
    chunks = pipeline.chunk_documents(documents)

    # Display stats
    stats = pipeline.get_chunk_stats(chunks)
    print(f"\nChunking Complete")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Chunk sizes (chars):")
    print(f"    Min: {stats['min_size']}")
    print(f"    Max: {stats['max_size']}")
    print(f"    Avg: {stats['avg_size']}")

    # Show sample chunks
    print(f"\nSample chunks:")
    for i in range(min(3, len(chunks))):
        chunk = chunks[i]
        print(f"\n  Chunk {i+1}:")
        print(f"    Source: {chunk.metadata.get('source_file', 'unknown')}")
        print(f"    Page: {chunk.metadata.get('page', 'N/A')}")
        print(f"    Size: {len(chunk.page_content)} chars")
        print(f"    Preview: {chunk.page_content[:150]}...")

    print(f"\nReady for vector storage (Step 3)")
