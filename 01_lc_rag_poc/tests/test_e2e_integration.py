"""
End-to-End Integration Test
Purpose: Validate complete RAG pipeline

Tests:
1. Document loading
2. Chunking and embedding
3. Vector storage
4. Retrieval
5. RAG answer generation
"""

import pytest
from pathlib import Path
from src.document_loader import DocumentLoader
from src.embedding_pipeline import EmbeddingPipeline
from src.vector_store import VectorStoreManager
from src.retriever import Retriever
from src.rag_chain import RAGChain


class TestE2EIntegration:
    """End-to-end integration tests"""

    @pytest.fixture(scope="class")
    def setup_pipeline(self):
        """Setup complete RAG pipeline"""
        print("\n🔧 Setting up RAG pipeline...")

        # 1. Load documents
        loader = DocumentLoader(data_dir="data/sample")
        documents = loader.load_documents()
        assert len(documents) > 0, "No documents loaded"
        print(f"Loaded {len(documents)} documents")

        # 2. Chunk documents
        pipeline = EmbeddingPipeline()
        chunks = pipeline.chunk_documents(documents)
        assert len(chunks) > 0, "No chunks created"
        print(f"Created {len(chunks)} chunks")

        # 3. Create vector store
        vector_manager = VectorStoreManager()
        # vector_manager.delete_collection()  # Clean slate
        vector_manager.delete_index()  # Clear old data
        vectorstore = vector_manager.create_vectorstore(chunks)
        assert vectorstore is not None, "Vector store creation failed"
        print(f"Vector store created")

        # 4. Initialize RAG chain
        rag_chain = RAGChain()
        print(f"RAG chain initialized")

        return {
            'documents': documents,
            'chunks': chunks,
            'vector_manager': vector_manager,
            'rag_chain': rag_chain
        }

    def test_document_loading(self, setup_pipeline):
        """Test 1: Document loading works"""
        documents = setup_pipeline['documents']

        assert len(documents) > 0
        assert all(hasattr(doc, 'page_content') for doc in documents)
        assert all('source_file' in doc.metadata for doc in documents)

        print("Test 1 passed: Document loading")

    def test_chunking(self, setup_pipeline):
        """Test 2: Chunking works"""
        chunks = setup_pipeline['chunks']

        assert len(chunks) > 0
        assert all(len(chunk.page_content) > 0 for chunk in chunks)
        assert all('chunk_id' in chunk.metadata for chunk in chunks)

        print("Test 2 passed: Chunking")

    def test_vector_store(self, setup_pipeline):
        """Test 3: Vector store works"""
        vector_manager = setup_pipeline['vector_manager']

        # Test retrieval
        results = vector_manager.similarity_search("machine learning", k=3)

        assert len(results) > 0
        assert len(results) <= 3
        assert all(isinstance(r.page_content, str) for r in results)

        print("Test 3 passed: Vector store retrieval")

    def test_retriever(self, setup_pipeline):
        """Test 4: Retriever works"""
        retriever = Retriever(vector_manager=setup_pipeline['vector_manager'])

        # Test retrieval
        documents = retriever.retrieve("What is AI?", k=2)

        assert len(documents) > 0
        assert len(documents) <= 2

        # Test formatting
        context = retriever.format_retrieved_context(documents)
        assert "Source 1:" in context
        assert len(context) > 0

        print("Test 4 passed: Retriever")

    def test_rag_answer_quality(self, setup_pipeline):
        """Test 5: RAG generates quality answers"""
        rag_chain = setup_pipeline['rag_chain']

        test_cases = [
            {
                'question': "What is machine learning?",
                'expected_keywords': ['machine', 'learning', 'data'],
                'should_have_sources': True
            },
            {
                'question': "What is quantum physics?",
                'expected_keywords': ["don't", 'information', 'enough'],
                'should_have_sources': False  # Off-topic
            }
        ]

        for case in test_cases:
            result = rag_chain.query(case['question'], k=3)

            # Check answer exists
            assert 'answer' in result
            assert len(result['answer']) > 0

            # Check for expected keywords
            answer_lower = result['answer'].lower()
            assert any(kw in answer_lower for kw in case['expected_keywords'])

            # Check sources
            if case['should_have_sources']:
                assert result['num_sources'] > 0

            print(f"Test case passed: {case['question'][:30]}...")

        print("Test 5 passed: RAG answer quality")

    def test_cost_tracking(self, setup_pipeline):
        """Test 6: Cost tracking works"""
        rag_chain = setup_pipeline['rag_chain']

        result = rag_chain.query_with_cost_tracking("What is AI?", k=2)

        assert 'cost' in result
        assert 'total_cost_usd' in result['cost']
        assert result['cost']['total_cost_usd'] > 0
        assert result['cost']['total_cost_usd'] < 0.01  # Should be cheap

        print(f"Test 6 passed: Cost tracking (${result['cost']['total_cost_usd']:.6f})")

    def test_performance(self, setup_pipeline):
        """Test 7: Performance is acceptable"""
        import time

        rag_chain = setup_pipeline['rag_chain']

        start = time.time()
        result = rag_chain.query("What is machine learning?", k=3)
        elapsed = time.time() - start

        # Should complete in under 5 seconds
        assert elapsed < 5.0, f"Query took too long: {elapsed:.2f}s"

        print(f"Test 7 passed: Performance ({elapsed:.2f}s)")


def run_e2e_tests():
    """Run all E2E tests"""
    print("\n" + "="*70)
    print("🧪 Running End-to-End Integration Tests")
    print("="*70 + "\n")

    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_e2e_tests()
