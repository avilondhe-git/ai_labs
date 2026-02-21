"""
RAG Chain with Azure OpenAI
Purpose: Complete RAG pipeline - retrieve + generate answer
"""

from typing import Dict
from openai import AzureOpenAI
from src.retriever import HybridRetriever
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger(__name__)


class RAGChain:
    """
    Complete RAG chain: Retrieval + Generation

    WHY: RAG combines:
         - Retrieval: Find relevant documents (external knowledge)
         - Generation: Generate answer using LLM + context
         - Result: Accurate answers grounded in your documents
    """

    def __init__(self):
        """Initialize RAG components"""

        self.retriever = HybridRetriever()

        # Azure OpenAI client for chat completion
        self.openai_client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint
        )

        self.chat_deployment = settings.azure_openai_chat_deployment

        logger.info(f"RAGChain initialized")
        logger.info(f"  Chat deployment: {self.chat_deployment}")

    def create_prompt(self, query: str, context: str) -> str:
        """
        Create RAG prompt with retrieved context

        WHY: Prompt engineering for RAG:
             - Provide clear instructions
             - Include source documents
             - Request source citations
             - Handle "I don't know" cases
        """
        prompt = f"""You are a helpful AI assistant that answers questions based on the provided documents.

**Instructions:**
- Answer the question using ONLY the information in the documents below
- If the answer is not in the documents, say "I don't have enough information to answer that question"
- Cite your sources by mentioning the document and page number
- Be concise and accurate

**Documents:**
{context}

**Question:** {query}

**Answer:**"""

        return prompt

    def generate_answer(self, query: str, context: str) -> Dict:
        """
        Generate answer using Azure OpenAI Chat

        Returns:
            Dict with answer and metadata
        """
        prompt = self.create_prompt(query, context)

        try:
            # WHY: Chat completion API for conversational responses
            response = self.openai_client.chat.completions.create(
                model=self.chat_deployment,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant specialized in answering questions based on provided documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # WHY: Low temperature for factual answers
                max_tokens=500
            )

            answer = response.choices[0].message.content

            return {
                "answer": answer,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "usage": {}
            }

    def query(self, question: str) -> Dict:
        """
        Complete RAG pipeline: retrieve + generate

        Args:
            question: User question

        Returns:
            Dict with answer, sources, and metadata
        """
        logger.info(f"Processing query: '{question}'")

        # Step 1: Retrieve relevant documents
        documents = self.retriever.retrieve(question)

        if not documents:
            return {
                "question": question,
                "answer": "I don't have any relevant documents to answer this question.",
                "sources": [],
                "usage": {}
            }

        # Step 2: Format context
        context = self.retriever.format_context(documents)

        # Step 3: Generate answer
        result = self.generate_answer(question, context)

        # Step 4: Compile response
        response = {
            "question": question,
            "answer": result["answer"],
            "sources": [
                {
                    "file": doc["metadata"].get("source_file"),
                    "page": doc["metadata"].get("page"),
                    "score": doc.get("score"),
                    "preview": doc["content"][:150] + "..."
                }
                for doc in documents
            ],
            "usage": result.get("usage", {})
        }

        logger.info(f"Query complete")
        return response


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    print("\n Testing RAG Chain...")

    rag_chain = RAGChain()

    # Test questions
    test_questions = [
        "What is retrieval augmented generation?",
        "How does machine learning work?",
        "What are the benefits of using embeddings?"
    ]

    for question in test_questions:
        print(f"\n{'='*80}")
        print(f"Question: {question}")
        print('='*80)

        # Get answer
        response = rag_chain.query(question)

        # Display answer
        print(f"\nAnswer:\n{response['answer']}\n")

        # Display sources
        print(f"Sources:")
        for idx, source in enumerate(response['sources'], 1):
            print(f"  {idx}. {source['file']}, Page {source['page']} (Score: {source['score']:.3f})")
            print(f"     Preview: {source['preview']}")

        # Display token usage
        usage = response.get('usage', {})
        print(f"\nToken Usage:")
        print(f"  Prompt: {usage.get('prompt_tokens', 0)}")
        print(f"  Completion: {usage.get('completion_tokens', 0)}")
        print(f"  Total: {usage.get('total_tokens', 0)}")
