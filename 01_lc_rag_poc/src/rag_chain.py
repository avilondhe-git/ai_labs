"""
RAG Chain
Purpose: Combine retrieval with generation for question answering

CV Mapping: RAG architecture, prompt engineering, LLM integration
"""

from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI

# Import ChatPromptTemplate (works with langchain 1.2.10 + Python 3.11)
try:
    from langchain.prompts import ChatPromptTemplate
except ImportError:
    from langchain_core.prompts import ChatPromptTemplate

# Import Document type
try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document

from src.retriever import Retriever
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class RAGChain:
    """
    Retrieval Augmented Generation chain

    WHY: Combines retrieval + generation for grounded, cited answers
    """

    def __init__(self, retriever: Optional[Retriever] = None):
        """
        Initialize RAG chain

        Args:
            retriever: Existing retriever (or create new)
        """
        # STEP 1: Initialize retriever
        self.retriever = retriever or Retriever()

        # STEP 2: Initialize LLM
        # WHY: gpt-4o-mini is cost-effective ($0.15/1M tokens) and fast
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,  # WHY: 0 for factual answers
            max_tokens=settings.max_tokens,
            openai_api_key=settings.openai_api_key
        )

        # STEP 3: Create prompt template
        # WHY: Structured prompt improves answer quality and citation
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant that answers questions based on provided context.

IMPORTANT RULES:
1. Only use information from the provided context
2. If the answer is not in the context, say "I don't have enough information to answer that question."
3. Always cite your sources using the format: [Source X]
4. Be concise but complete
5. If multiple sources provide similar information, mention all relevant sources

Context:
{context}"""),
            ("human", "{question}")
        ])

        logger.info("RAG Chain initialized")
        logger.info(f"  LLM: {settings.llm_model}")
        logger.info(f"  Temperature: {settings.llm_temperature}")
        logger.info(f"  Max tokens: {settings.max_tokens}")

    def query(
        self,
        question: str,
        k: Optional[int] = None,
        return_sources: bool = True
    ) -> Dict:
        """
        Answer question using RAG

        Args:
            question: User question
            k: Number of documents to retrieve
            return_sources: Whether to return source documents

        Returns:
            Dictionary with 'answer', 'sources', and metadata
        """
        logger.info(f"Processing query: '{question[:50]}...'")

        # STEP 1: Retrieve relevant documents
        documents = self.retriever.retrieve(question, k=k)

        if not documents:
            logger.warning("No documents retrieved")
            return {
                "answer": "I don't have any relevant information to answer that question.",
                "sources": [],
                "num_sources": 0
            }

        # STEP 2: Format context
        context = self.retriever.format_retrieved_context(documents)

        # STEP 3: Generate answer
        logger.info("Generating answer with LLM...")

        # WHY: Invoke chain with formatted prompt
        messages = self.prompt.format_messages(
            context=context,
            question=question
        )

        response = self.llm.invoke(messages)
        answer = response.content

        logger.info(f"Answer generated ({len(answer)} chars)")

        # STEP 4: Prepare response
        result = {
            "answer": answer,
            "num_sources": len(documents),
            "tokens_used": response.response_metadata.get('token_usage', {})
        }

        if return_sources:
            # WHY: Include source metadata for citations
            result["sources"] = [
                {
                    "file": doc.metadata.get('source_file', 'unknown'),
                    "page": doc.metadata.get('page', 'N/A'),
                    "content": doc.page_content[:200] + "..."
                }
                for doc in documents
            ]

        return result

    def query_with_cost_tracking(self, question: str, k: Optional[int] = None) -> Dict:
        """
        Query with detailed cost tracking

        WHY: Important for production cost management

        Returns:
            Response dict with added cost information
        """
        result = self.query(question, k=k, return_sources=True)

        # Calculate costs
        tokens = result.get('tokens_used', {})
        prompt_tokens = tokens.get('prompt_tokens', 0)
        completion_tokens = tokens.get('completion_tokens', 0)

        # WHY: GPT-4o-mini pricing (as of Jan 2026)
        # Input: $0.15 per 1M tokens
        # Output: $0.60 per 1M tokens
        input_cost = (prompt_tokens / 1_000_000) * 0.15
        output_cost = (completion_tokens / 1_000_000) * 0.60
        total_cost = input_cost + output_cost

        result['cost'] = {
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': prompt_tokens + completion_tokens,
            'input_cost_usd': round(input_cost, 6),
            'output_cost_usd': round(output_cost, 6),
            'total_cost_usd': round(total_cost, 6)
        }

        logger.info(f"Query cost: ${total_cost:.6f} USD")

        return result


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    import time

    print("\n🤖 Initializing RAG Chain...")

    try:
        rag = RAGChain()
    except Exception as e:
        print(f"Error: {e}")
        print("\nPlease ensure:")
        print("1. Vector store exists (run: python src/vector_store.py)")
        print("2. OPENAI_API_KEY is set in .env file")
        exit(1)

    print("RAG Chain ready\n")

    # Test questions
    test_questions = [
        "What is artificial intelligence and what are its key areas?",
        "Explain the different types of machine learning",
        "How does RAG work and what are its benefits?",
        "What is deep learning?",  # Not in our docs - should say "don't know"
    ]

    total_cost = 0.0

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*70}")
        print(f"Question {i}/{len(test_questions)}: {question}")
        print(f"{'='*70}\n")

        start_time = time.time()

        # Get answer with cost tracking
        result = rag.query_with_cost_tracking(question, k=3)

        elapsed = time.time() - start_time

        # Display answer
        print(f"Answer:\n{result['answer']}\n")

        # Display sources
        print(f"Sources Used: {result['num_sources']}")
        for j, source in enumerate(result.get('sources', []), 1):
            print(f"  {j}. {source['file']}, page {source['page']}")

        # Display performance
        cost_info = result['cost']
        total_cost += cost_info['total_cost_usd']

        print(f"\nPerformance:")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Tokens: {cost_info['total_tokens']} "
              f"(prompt: {cost_info['prompt_tokens']}, "
              f"completion: {cost_info['completion_tokens']})")
        print(f"  Cost: ${cost_info['total_cost_usd']:.6f} USD")

    print(f"\n{'='*70}")
    print(f"All questions processed!")
    print(f"Total cost: ${total_cost:.6f} USD")
    print(f"Average cost per query: ${total_cost/len(test_questions):.6f} USD")
