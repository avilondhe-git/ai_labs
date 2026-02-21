"""
Test Data Generator
Purpose: Create sample PDF files for testing
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pathlib import Path

def create_test_pdf(filename: str, content: str, num_pages: int = 3):
    """Create a simple test PDF with content"""
    output_dir = Path("data/sample")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_path = output_dir / filename
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    
    for page_num in range(num_pages):
        # Add page number
        c.drawString(50, 750, f"Page {page_num + 1} of {num_pages}")
        
        # Add content
        text_object = c.beginText(50, 700)
        text_object.setFont("Helvetica", 12)
        
        # Split content into lines
        lines = content.split('\n')
        for line in lines:
            text_object.textLine(line)
        
        c.drawText(text_object)
        c.showPage()
    
    c.save()
    print(f"Created: {pdf_path}")

if __name__ == "__main__":
    # Sample document 1: AI Overview
    create_test_pdf(
        "ai_overview.pdf",
        """
        Artificial Intelligence Overview
        
        Artificial Intelligence (AI) is the simulation of human intelligence 
        processes by machines, especially computer systems. These processes 
        include learning, reasoning, and self-correction.
        
        Key Areas of AI:
        - Machine Learning: Algorithms that improve through experience
        - Natural Language Processing: Understanding human language
        - Computer Vision: Interpreting visual information
        - Robotics: Physical embodiment of AI systems
        
        Applications:
        - Healthcare: Disease diagnosis and treatment planning
        - Finance: Fraud detection and algorithmic trading
        - Transportation: Autonomous vehicles
        - Entertainment: Recommendation systems
        """,
        num_pages=2
    )
    
    # Sample document 2: Machine Learning
    create_test_pdf(
        "machine_learning.pdf",
        """
        Machine Learning Fundamentals
        
        Machine Learning is a subset of AI that enables systems to learn 
        and improve from experience without being explicitly programmed.
        
        Types of Machine Learning:
        1. Supervised Learning: Learning from labeled data
        2. Unsupervised Learning: Finding patterns in unlabeled data
        3. Reinforcement Learning: Learning through trial and error
        
        Common Algorithms:
        - Linear Regression: Predicting continuous values
        - Decision Trees: Classification and regression
        - Neural Networks: Deep learning models
        - K-Means: Clustering algorithm
        
        Evaluation Metrics:
        - Accuracy: Percentage of correct predictions
        - Precision: Ratio of true positives
        - Recall: Ratio of actual positives found
        - F1 Score: Harmonic mean of precision and recall
        """,
        num_pages=3
    )
    
    # Sample document 3: RAG Systems
    create_test_pdf(
        "rag_systems.pdf",
        """
        Retrieval Augmented Generation (RAG)
        
        RAG is a technique that combines information retrieval with 
        generative AI to produce more accurate and grounded responses.
        
        How RAG Works:
        1. Document Ingestion: Load and process documents
        2. Embedding: Convert text to vector representations
        3. Storage: Store embeddings in vector database
        4. Retrieval: Find relevant documents for a query
        5. Generation: Use LLM to generate answer with context
        
        Benefits:
        - Reduces hallucinations by grounding in real data
        - Enables knowledge updates without retraining
        - Provides source citations for answers
        - Cost-effective compared to fine-tuning
        
        Components:
        - Vector Database: FAISS, Pinecone, Qdrant, Weaviate
        - Embeddings: OpenAI, Cohere, Sentence Transformers
        - LLMs: GPT-4, Claude, Llama
        - Frameworks: LangChain, LlamaIndex
        """,
        num_pages=3
    )
    
    print("\nGenerated 3 test PDF files in data/sample/")
    print("  You can now run: python src/document_loader.py")
