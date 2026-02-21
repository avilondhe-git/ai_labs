"""
Azure Blob Storage Document Loader
Purpose: Upload and load documents from Azure Blob Storage
"""

from pathlib import Path
from typing import List, Dict
from azure.storage.blob import BlobServiceClient
from pypdf import PdfReader
from io import BytesIO
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class AzureBlobDocumentLoader:
    """
    Loads documents from Azure Blob Storage

    WHY: Azure Blob Storage provides:
         - Durable cloud storage
         - Version history
         - Access from anywhere
         - Integration with Azure services
    """

    def __init__(self):
        """Initialize Azure Blob Storage client"""
        self.connection_string = settings.azure_storage_connection_string
        self.container_name = settings.azure_storage_container_name

        # WHY: BlobServiceClient handles authentication and connection pooling
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        self.container_client = self.blob_service_client.get_container_client(
            self.container_name
        )

        logger.info(f"AzureBlobDocumentLoader initialized")
        logger.info(f"  Container: {self.container_name}")

    def upload_documents(self, local_dir: str) -> List[str]:
        """
        Upload PDF files from local directory to Blob Storage

        Args:
            local_dir: Local directory containing PDFs

        Returns:
            List of uploaded blob names
        """
        local_path = Path(local_dir)
        pdf_files = list(local_path.glob("*.pdf"))

        if not pdf_files:
            logger.warning(f"No PDF files found in {local_dir}")
            return []

        uploaded_blobs = []

        for pdf_file in pdf_files:
            try:
                blob_name = pdf_file.name
                blob_client = self.container_client.get_blob_client(blob_name)

                # Upload file
                with open(pdf_file, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)

                uploaded_blobs.append(blob_name)
                logger.info(f"Uploaded: {blob_name}")

            except Exception as e:
                logger.error(f"Failed to upload {pdf_file.name}: {e}")
                continue

        logger.info(f"Uploaded {len(uploaded_blobs)} documents")
        return uploaded_blobs

    def load_documents(self) -> List[Dict]:
        """
        Load documents from Blob Storage and extract text

        Returns:
            List of dictionaries with document content and metadata
        """
        documents = []

        # List all blobs in container
        blob_list = self.container_client.list_blobs()
        pdf_blobs = [blob for blob in blob_list if blob.name.endswith('.pdf')]

        if not pdf_blobs:
            logger.warning(f"No PDF files found in container")
            return documents

        logger.info(f"Found {len(pdf_blobs)} PDF files")

        for blob in pdf_blobs:
            try:
                # Download blob content
                blob_client = self.container_client.get_blob_client(blob.name)
                blob_data = blob_client.download_blob().readall()

                # Extract text from PDF
                pdf_reader = PdfReader(BytesIO(blob_data))

                # Process each page
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()

                    if text.strip():  # Skip empty pages
                        doc = {
                            "page_content": text,
                            "metadata": {
                                "source_file": blob.name,
                                "page": page_num,
                                "total_pages": len(pdf_reader.pages)
                            }
                        }
                        documents.append(doc)

                logger.info(f"Loaded {blob.name}: {len(pdf_reader.pages)} pages")

            except Exception as e:
                logger.error(f"Failed to load {blob.name}: {e}")
                continue

        logger.info(f"Total documents loaded: {len(documents)}")
        return documents

    def get_document_stats(self, documents: List[Dict]) -> Dict:
        """Get statistics about loaded documents"""
        if not documents:
            return {"total_docs": 0, "total_chars": 0, "avg_chars_per_doc": 0}

        total_chars = sum(len(doc["page_content"]) for doc in documents)

        # Group by source file
        files = {}
        for doc in documents:
            source = doc["metadata"].get("source_file", "unknown")
            files[source] = files.get(source, 0) + 1

        return {
            "total_docs": len(documents),
            "total_chars": total_chars,
            "avg_chars_per_doc": total_chars // len(documents),
            "files": files
        }


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    print("\n Uploading documents to Azure Blob Storage...")

    loader = AzureBlobDocumentLoader()

    # Upload documents from local directory
    uploaded = loader.upload_documents("data/sample")

    if not uploaded:
        print("\n  No documents uploaded. Add PDFs to data/sample/")
        exit(1)

    print(f"Uploaded {len(uploaded)} files")

    # Load documents from Blob Storage
    print("\n Loading documents from Azure Blob Storage...")
    documents = loader.load_documents()

    if not documents:
        print("No documents found")
        exit(1)

    # Display stats
    stats = loader.get_document_stats(documents)

    print(f"\n Document Loading Complete")
    print(f"  Total documents: {stats['total_docs']}")
    print(f"  Total characters: {stats['total_chars']:,}")
    print(f"  Average per document: {stats['avg_chars_per_doc']:,}")
    print(f"\n  Files loaded:")
    for filename, page_count in stats['files'].items():
        print(f"    - {filename}: {page_count} pages")

    # Show sample content
    print(f"\n Sample content from first document:")
    print(f"  Source: {documents[0]['metadata'].get('source_file')}")
    print(f"  Page: {documents[0]['metadata'].get('page')}")
    print(f"  Content preview: {documents[0]['page_content'][:200]}...")
