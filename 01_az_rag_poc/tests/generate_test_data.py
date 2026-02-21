"""
Generate Test PDF Documents
Purpose: Create sample PDFs for testing the RAG system
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from pathlib import Path


def create_test_pdf(filename: str, title: str, content: list):
    """Create a PDF with given content"""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add title
    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 12))
    
    # Add content
    for text in content:
        story.append(Paragraph(text, styles['BodyText']))
        story.append(Spacer(1, 12))
    
    doc.build(story)


def generate_all_test_documents():
    """Generate a set of test documents"""
    output_dir = Path("data/sample")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Document 1: AI Overview
    create_test_pdf(
        str(output_dir / "ai_overview.pdf"),
        "Artificial Intelligence Overview",
        [
            "Artificial intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving.",
            "AI research has been highly successful in developing effective techniques for solving a wide range of problems, from game playing to medical diagnosis. Modern AI systems are capable of processing vast amounts of data and identifying patterns that would be impossible for humans to discern.",
            "Machine learning, a subset of AI, enables systems to automatically learn and improve from experience without being explicitly programmed. Deep learning, an advanced form of machine learning, uses neural networks with multiple layers to progressively extract higher-level features from raw input."
        ]
    )
    
    # Document 2: Machine Learning
    create_test_pdf(
        str(output_dir / "machine_learning.pdf"),
        "Machine Learning Fundamentals",
        [
            "Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
            "There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Supervised learning algorithms learn from labeled training data and make predictions. Unsupervised learning finds hidden patterns in data without pre-existing labels.",
            "Popular machine learning algorithms include linear regression, logistic regression, decision trees, random forests, support vector machines, and neural networks. Each algorithm has its strengths and is suited to different types of problems.",
            "The machine learning workflow typically involves data collection, data preparation, choosing a model, training the model, evaluation, parameter tuning, and prediction. Feature engineering and selection are critical steps that can significantly impact model performance."
        ]
    )
    
    # Document 3: RAG Systems
    create_test_pdf(
        str(output_dir / "rag_systems.pdf"),
        "Retrieval Augmented Generation Systems",
        [
            "Retrieval Augmented Generation (RAG) is a technique that enhances large language models by retrieving relevant documents from an external knowledge base before generating a response. This approach combines the strengths of retrieval-based and generation-based methods.",
            "RAG systems consist of two main components: a retriever that finds relevant documents and a generator (typically a large language model) that produces answers based on the retrieved context. The retriever uses techniques like vector similarity search to find the most relevant documents.",
            "Embeddings play a crucial role in RAG systems. Documents and queries are converted into dense vector representations using embedding models. These vectors capture semantic meaning, enabling the system to find conceptually similar documents even if they don't share exact keywords.",
            "Hybrid search combines vector similarity search with traditional keyword-based search (like BM25) to improve retrieval quality. This approach leverages both semantic understanding and exact term matching, often producing better results than either method alone.",
            "RAG systems offer several advantages: they can access up-to-date information, provide source citations for verification, reduce hallucinations by grounding responses in retrieved documents, and allow customization without retraining the language model."
        ]
    )
    
    print(f"Generated 3 test PDF documents in {output_dir}")
    print(f"  - ai_overview.pdf")
    print(f"  - machine_learning.pdf")
    print(f"  - rag_systems.pdf")


if __name__ == "__main__":
    print("\n📄 Generating Test Documents...")
    generate_all_test_documents()
    print("\nTest documents ready for upload!")
