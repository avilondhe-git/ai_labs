"""
Streamlit Web UI for RAG System
Purpose: Interactive interface for document Q&A
"""

import streamlit as st
from src.rag_chain import RAG Chain
from src.utils.logger import get_logger

logger = get_logger(__name__)


# WHY: Page config must be  first Streamlit command
st.set_page_config(
    page_title="Azure RAG Document Intelligence",
    page_icon="🔍",
    layout="wide"
)


@st.cache_resource
def load_rag_chain():
    """
    Load RAG chain (cached for performance)

    WHY: @st.cache_resource ensures RAG chain is initialized once
         and reused across sessions (faster, more efficient)
    """
    return RAGChain()


def display_sources(sources):
    """Display source documents in expandable sections"""
    st.subheader("Sources")

    for idx, source in enumerate(sources, 1):
        with st.expander(f"Source {idx}: {source['file']} (Page {source['page']}) - Score: {source['score']:.3f}"):
            st.text(source['preview'])


def main():
    """Main Streamlit application"""

    # Title and description
    st.title("Azure RAG Document Intelligence")
    st.markdown("""
    Ask questions about your documents and get AI-powered answers with source citations.

    **Powered by:**
    - Azure Blob Storage (document storage)
    - Azure OpenAI (embeddings + chat)
    - Azure AI Search (hybrid search)
    """)

    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Load RAG chain
    try:
        rag_chain = load_rag_chain()
    except Exception as e:
        st.error(f"Failed to initialize RAG system: {str(e)}")
        st.stop()

    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")

        show_debug = st.checkbox("Show debug info", value=False)

        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This RAG system uses Azure AI services to:
        1. Store documents in Blob Storage
        2. Generate embeddings with Azure OpenAI
        3. Index with Azure AI Search (hybrid search)
        4. Answer questions using GPT-4o-mini
        """)

        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant" and "sources" in message:
                display_sources(message["sources"])

                if show_debug and "usage" in message:
                    st.caption(f"Tokens: {message['usage'].get('total_tokens', 0)}")

    # Question input
    if question := st.chat_input("Ask a question about your documents..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Get answer from RAG chain
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = rag_chain.query(question)

                    # Display answer
                    st.markdown(response["answer"])

                    # Display sources
                    if response["sources"]:
                        display_sources(response["sources"])

                    # Debug info
                    if show_debug:
                        st.caption(f"Token usage: {response['usage'].get('total_tokens', 0)} tokens")

                    # Add to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["answer"],
                        "sources": response["sources"],
                        "usage": response["usage"]
                    })

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    logger.error(f"Query failed: {e}")


if __name__ == "__main__":
    main()
