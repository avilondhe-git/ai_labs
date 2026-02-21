"""
Streamlit UI for RAG Document Intelligence
Purpose: User-friendly web interface for document Q&A

CV Mapping: Full-stack development, UI/UX, production deployment
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import time
from src.document_loader import DocumentLoader
from src.embedding_pipeline import EmbeddingPipeline
from src.vector_store import VectorStoreManager
from src.rag_chain import RAGChain

# Page config
st.set_page_config(
    page_title="RAG Document Intelligence",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'rag_chain' not in st.session_state:
    st.session_state.rag_chain = None
if 'documents_loaded' not in st.session_state:
    st.session_state.documents_loaded = False
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0


def initialize_rag_system():
    """Initialize or load RAG system"""
    try:
        # Try to load existing vector store
        vector_manager = VectorStoreManager()
        loaded = vector_manager.load_vectorstore()

        if loaded:
            st.session_state.rag_chain = RAGChain()
            st.session_state.documents_loaded = True
            return True, "Loaded existing document collection"
        else:
            return False, "No documents found. Please upload documents first."

    except Exception as e:
        return False, f"Error initializing system: {e}"


def process_documents():
    """Process uploaded documents and create vector store"""
    with st.spinner("Processing documents..."):
        # Load documents
        loader = DocumentLoader(data_dir="data/sample")
        documents = loader.load_documents()

        if not documents:
            return False, "No PDF files found in data/sample/"

        # Chunk documents
        pipeline = EmbeddingPipeline()
        chunks = pipeline.chunk_documents(documents)

        # Create vector store
        vector_manager = VectorStoreManager()
        # vector_manager.delete_collection()  # Clear old data
        vector_manager.delete_index()  # Clear old data
        vector_manager.create_vectorstore(chunks)

        # Initialize RAG chain
        st.session_state.rag_chain = RAGChain()
        st.session_state.documents_loaded = True

        stats = loader.get_document_stats(documents)

        return True, f"""
        Successfully processed documents:
        - Documents: {stats['total_docs']}
        - Files: {len(stats['files'])}
        - Chunks created: {len(chunks)}
        """


def main():
    # Header
    st.title("RAG Document Intelligence System")
    st.markdown("Ask questions about your documents and get answers with citations")

    # Sidebar
    with st.sidebar:
        st.header("System Status")

        # Initialize button
        if st.button("Initialize System"):
            success, message = initialize_rag_system()
            if success:
                st.success(message)
            else:
                st.warning(message)

        # Process documents button
        if st.button("Process Documents"):
            success, message = process_documents()
            if success:
                st.success(message)
            else:
                st.error(message)

        # Status indicators
        st.markdown("---")
        if st.session_state.documents_loaded:
            st.success("System Ready")
        else:
            st.warning("No Documents Loaded")

        # Stats
        if st.session_state.query_history:
            st.markdown("---")
            st.subheader("Usage Stats")
            st.metric("Total Queries", len(st.session_state.query_history))
            st.metric("Total Cost", f"${st.session_state.total_cost:.6f}")
            st.metric("Avg Cost/Query",
                     f"${st.session_state.total_cost/len(st.session_state.query_history):.6f}")

        # Instructions
        st.markdown("---")
        st.subheader("Instructions")
        st.markdown("""
        1. Place PDF files in `data/sample/` folder
        2. Click **Process Documents**
        3. Ask questions in the main panel
        4. View answers with sources
        """)

    # Main panel
    if not st.session_state.documents_loaded:
        st.info("Please initialize the system using the sidebar")

        st.markdown("""
        ### Getting Started

        1. **Add Documents**: Place PDF files in `data/sample/` directory
        2. **Process**: Click "Process Documents" in the sidebar
        3. **Query**: Start asking questions!

        ### Sample Questions
        - What is artificial intelligence?
        - Explain machine learning types
        - How does RAG work?
        """)

    else:
        # Query interface
        st.subheader("💬 Ask a Question")

        # Question input
        question = st.text_input(
            "Enter your question:",
            placeholder="e.g., What is machine learning?",
            key="question_input"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            k_results = st.selectbox("Sources to retrieve:", [2, 3, 4, 5], index=1)

        if st.button("Get Answer", type="primary"):
            if question:
                with st.spinner("Searching documents and generating answer..."):
                    start_time = time.time()

                    # Get answer
                    result = st.session_state.rag_chain.query_with_cost_tracking(
                        question, k=k_results
                    )

                    elapsed = time.time() - start_time

                    # Update stats
                    st.session_state.total_cost += result['cost']['total_cost_usd']
                    st.session_state.query_history.append({
                        'question': question,
                        'answer': result['answer'],
                        'cost': result['cost']['total_cost_usd'],
                        'time': elapsed
                    })

                # Display answer
                st.markdown("---")
                st.subheader("Answer")
                st.markdown(result['answer'])

                # Display sources
                st.markdown("---")
                st.subheader("Sources")
                for i, source in enumerate(result.get('sources', []), 1):
                    with st.expander(f"Source {i}: {source['file']}, page {source['page']}"):
                        st.text(source['content'])

                # Display metrics
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("⏱️ Response Time", f"{elapsed:.2f}s")
                with col2:
                    st.metric("🪙 Tokens Used", result['cost']['total_tokens'])
                with col3:
                    st.metric("💰 Cost", f"${result['cost']['total_cost_usd']:.6f}")

            else:
                st.warning("Please enter a question")

        # Query history
        if st.session_state.query_history:
            st.markdown("---")
            st.subheader("📜 Query History")

            for i, query in enumerate(reversed(st.session_state.query_history[-5:]), 1):
                with st.expander(f"Q{len(st.session_state.query_history)-i+1}: {query['question'][:50]}..."):
                    st.markdown(f"**Question:** {query['question']}")
                    st.markdown(f"**Answer:** {query['answer'][:200]}...")
                    st.caption(f"Time: {query['time']:.2f}s | Cost: ${query['cost']:.6f}")


if __name__ == "__main__":
    main()
