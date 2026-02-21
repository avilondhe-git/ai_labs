"""
Document Loader
Purpose: Load and extract text from PDF documents

CV Mapping: Document processing pipelines, PDF parsing, metadata extraction
"""

from pathlib import Path
from typing import List, Dict, Any
from langchain_community.document_loaders import PyPDFLoader
# from langchain.schema import Document
# try all known locations; if none are available, fall back to Any
try:
    from langchain.schema import Document
except ImportError:
    try:
        from langchain_core.schema import Document
    except ImportError:
        try:
            from langchain.docstore.document import Document
        except ImportError:
            Document = Any   # no langchain installed

from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class DocumentLoader:
    """
    Loads documents from various file formats

    WHY: Centralized document loading enables easy format expansion
         (PDF today, DOCX/TXT tomorrow)
    """

    def __init__(self, data_dir: str = "data/sample"):
        """
        Initialize document loader

        Args:
            data_dir: Directory containing documents to load
        """
        self.data_dir = Path(data_dir)
        self.supported_extensions = ['.pdf']

        # WHY: Create directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"DocumentLoader initialized for: {self.data_dir}")

    def load_documents(self) -> List[Document]:
        """
        Load all supported documents from directory

        WHY: Batch loading is more efficient than one-by-one

        Returns:
            List of Document objects with content and metadata
        """
        documents = []

        # STEP 1: Find all PDF files
        pdf_files = list(self.data_dir.glob("*.pdf"))

        if not pdf_files:
            logger.warning(f"No PDF files found in {self.data_dir}")
            return documents

        logger.info(f"Found {len(pdf_files)} PDF files")

        # STEP 2: Load each PDF
        for pdf_path in pdf_files:
            try:
                docs = self._load_pdf(pdf_path)
                documents.extend(docs)
                logger.info(f"Loaded {pdf_path.name}: {len(docs)} pages")

            except Exception as e:
                logger.error(f"Failed to load {pdf_path.name}: {e}")
                continue

        logger.info(f"Total documents loaded: {len(documents)}")
        return documents

    def _load_pdf(self, file_path: Path) -> List[Document]:
        """
        Load a single PDF file

        WHY: PyPDFLoader handles page-by-page extraction with metadata

        Args:
            file_path: Path to PDF file

        Returns:
            List of Document objects (one per page)
        """
        # WHY: LangChain's PyPDFLoader preserves page numbers
        loader = PyPDFLoader(str(file_path))
        documents = loader.load()

        # STEP 3: Enrich metadata
        for doc in documents:
            doc.metadata['source_file'] = file_path.name
            # WHY: Original 'source' contains full path, cleaner to have just filename

        return documents

    def get_document_stats(self, documents: List[Document]) -> Dict:
        """
        Get statistics about loaded documents

        WHY: Useful for validation and debugging

        Args:
            documents: List of Document objects

        Returns:
            Dictionary with stats
        """
        if not documents:
            return {"total_docs": 0, "total_chars": 0, "avg_chars_per_doc": 0}

        total_chars = sum(len(doc.page_content) for doc in documents)

        # Group by source file
        files = {}
        for doc in documents:
            source = doc.metadata.get('source_file', 'unknown')
            if source not in files:
                files[source] = 0
            files[source] += 1

        stats = {
            "total_docs": len(documents),
            "total_chars": total_chars,
            "avg_chars_per_doc": total_chars // len(documents),
            "files": files
        }

        return stats


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    # Initialize loader
    loader = DocumentLoader(data_dir="data/sample")

    # Load documents
    print("\n📄 Loading documents...")
    documents = loader.load_documents()

    if not documents:
        print("\nNo documents found in data/sample/")
        print("Please add PDF files to data/sample/ directory")
        exit(1)

    # Display stats
    stats = loader.get_document_stats(documents)

    print(f"\nDocument Loading Complete")
    print(f"  Total documents: {stats['total_docs']}")
    print(f"  Total characters: {stats['total_chars']:,}")
    print(f"  Average per document: {stats['avg_chars_per_doc']:,}")
    print(f"\n  Files loaded:")
    for filename, page_count in stats['files'].items():
        print(f"    - {filename}: {page_count} pages")

    # Show sample content
    print(f"\nSample content from first document:")
    print(f"  Source: {documents[0].metadata.get('source_file')}")
    print(f"  Page: {documents[0].metadata.get('page', 'N/A')}")
    print(f"  Content preview: {documents[0].page_content[:200]}...")
