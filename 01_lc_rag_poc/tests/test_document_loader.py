"""
Unit tests for document loader
"""

import pytest
from pathlib import Path
from src.document_loader import DocumentLoader

def test_document_loader_initialization():
    """Test loader initializes correctly"""
    loader = DocumentLoader(data_dir="data/sample")
    assert loader.data_dir.exists()
    assert loader.supported_extensions == ['.pdf']

def test_load_documents():
    """Test loading sample documents"""
    loader = DocumentLoader(data_dir="data/sample")
    documents = loader.load_documents()

    # Should have documents if PDFs exist
    if documents:
        assert len(documents) > 0

        # Check document structure
        doc = documents[0]
        assert hasattr(doc, 'page_content')
        assert hasattr(doc, 'metadata')
        assert 'source_file' in doc.metadata

        # Content should not be empty
        assert len(doc.page_content) > 50

def test_document_stats():
    """Test statistics calculation"""
    loader = DocumentLoader(data_dir="data/sample")
    documents = loader.load_documents()

    if documents:
        stats = loader.get_document_stats(documents)

        assert 'total_docs' in stats
        assert 'total_chars' in stats
        assert 'avg_chars_per_doc' in stats
        assert 'files' in stats

        assert stats['total_docs'] == len(documents)
        assert stats['total_chars'] > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
