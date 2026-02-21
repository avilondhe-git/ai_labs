"""
Azure OpenAI Embedding Pipeline
Purpose: Chunk documents and generate embeddings for semantic search
"""

from typing import List, Dict
import tiktoken
from openai import AzureOpenAI
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class TextChunker:
    """
    Split documents into chunks for embedding

    WHY: Large documents exceed embedding model limits (8191 tokens for ada-002)
         Chunking also improves retrieval precision - smaller chunks = more specific matches
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Args:
            chunk_size: Target characters per chunk
            chunk_overlap: Characters to overlap between chunks (preserves context)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # WHY: tiktoken counts *tokens* not characters - important for OpenAI models
        self.encoding = tiktoken.encoding_for_model("text-embedding-ada-002")

        logger.info(f"TextChunker initialized")
        logger.info(f"  Chunk size: {chunk_size} chars")
        logger.info(f"  Overlap: {chunk_overlap} chars")

    def split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""

        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Find last period or newline to avoid cutting sentences
            if end < len(text):
                last_period = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                if last_period > start or last_newline > start:
                    end = max(last_period, last_newline) + 1

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap

            # Avoid infinite loops
            if start >= len(text):
                break

        return chunks

    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Split documents into chunks while preserving metadata

        Args:
            documents: List of {page_content, metadata} dicts

        Returns:
            List of chunked documents with updated metadata
        """
        chunked_docs = []

        for doc in documents:
            text = doc["page_content"]
            metadata = doc["metadata"]

            # Split into chunks
            chunks = self.split_text(text)

            # Create document for each chunk
            for chunk_idx, chunk in enumerate(chunks):
                chunked_doc = {
                    "page_content": chunk,
                    "metadata": {
                        **metadata,
                        "chunk": chunk_idx,
                        "total_chunks": len(chunks)
                    }
                }
                chunked_docs.append(chunked_doc)

        logger.info(f"Chunked {len(documents)} docs into {len(chunked_docs)} chunks")
        return chunked_docs

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))


class AzureOpenAIEmbedder:
    """
    Generate embeddings using Azure OpenAI

    WHY: Azure OpenAI provides:
         - Same models as OpenAI but hosted in Azure
         - Enterprise features (VNet, Private Link, RBAC)
         - Data residency guarantees
    """

    def __init__(self):
        """Initialize Azure OpenAI client"""

        # WHY: AzureOpenAI client handles authentication and retries
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint
        )

        self.deployment = settings.azure_openai_embedding_deployment

        logger.info(f"AzureOpenAIEmbedder initialized")
        logger.info(f"  Endpoint: {settings.azure_openai_endpoint}")
        logger.info(f"  Deployment: {self.deployment}")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text

        Returns:
            1536-dimensional embedding vector
        """
        response = self.client.embeddings.create(
            input=text,
            model=self.deployment
        )

        return response.data[0].embedding

    def embed_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for all documents

        WHY: Batch processing is more efficient but Azure OpenAI has limits:
             - Max 16 texts per batch
             - Max 8191 tokens per text
        """
        embedded_docs = []

        # WHY: Process in batches of 16 (Azure OpenAI limit)
        batch_size = 16
        total_batches = (len(documents) + batch_size - 1) // batch_size

        logger.info(f"Embedding {len(documents)} documents in {total_batches} batches...")

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_texts = [doc["page_content"] for doc in batch]

            try:
                # Generate embeddings for batch
                response = self.client.embeddings.create(
                    input=batch_texts,
                    model=self.deployment
                )

                # Add embeddings to documents
                for doc, embedding_data in zip(batch, response.data):
                    embedded_doc = {
                        **doc,
                        "embedding": embedding_data.embedding
                    }
                    embedded_docs.append(embedded_doc)

                logger.info(f"  Batch {i//batch_size + 1}/{total_batches} complete")

            except Exception as e:
                logger.error(f"Batch {i//batch_size + 1} failed: {e}")
                continue

        logger.info(f"Generated {len(embedded_docs)} embeddings")
        return embedded_docs


class EmbeddingPipeline:
    """Complete embedding pipeline: chunk + embed"""

    def __init__(self):
        self.chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self.embedder = AzureOpenAIEmbedder()

    def process_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Complete pipeline: chunk documents and generate embeddings

        Returns:
            Documents with embeddings added
        """
        logger.info("Starting embedding pipeline...")

        # Step 1: Chunk documents
        chunked_docs = self.chunker.chunk_documents(documents)

        # Step 2: Generate embeddings
        embedded_docs = self.embedder.embed_documents(chunked_docs)

        logger.info("Embedding pipeline complete")
        return embedded_docs


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    from src.azure_blob_loader import AzureBlobDocumentLoader

    print("\n Loading documents from Azure Blob Storage...")
    loader = AzureBlobDocumentLoader()
    documents = loader.load_documents()

    if not documents:
        print("No documents found")
        exit(1)

    print(f"Loaded {len(documents)} documents")

    # Initialize pipeline
    print("\n Processing embedding pipeline...")
    pipeline = EmbeddingPipeline()

    # Process documents
    embedded_docs = pipeline.process_documents(documents)

    print(f"\n Embedding Pipeline Complete")
    print(f"  Total embedded chunks: {len(embedded_docs)}")
    print(f"  Embedding dimensions: {len(embedded_docs[0]['embedding'])}")

    # Show sample
    print(f"\n Sample embedded chunk:")
    sample = embedded_docs[0]
    print(f"  Source: {sample['metadata'].get('source_file')}")
    print(f"  Chunk: {sample['metadata'].get('chunk')} / {sample['metadata'].get('total_chunks')}")
    print(f"  Content: {sample['page_content'][:150]}...")
    print(f"  Embedding: [{sample['embedding'][0]:.6f}, {sample['embedding'][1]:.6f}, ..., {sample['embedding'][-1]:.6f}]")
