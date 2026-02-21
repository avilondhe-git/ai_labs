"""
Configuration Management
Purpose: Load and validate environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

class Settings(BaseModel):
    """Application settings"""
    
    # OpenAI
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    embedding_model: str = Field(default="text-embedding-3-small")
    llm_model: str = Field(default="gpt-4o-mini")
    llm_temperature: float = Field(default=0.0)
    
    # Vector Store
    vector_store_path: str = Field(default="./data/processed/faiss_index")
    collection_name: str = Field(default="document_collection")
    
    # Chunking
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    
    # Retrieval
    top_k_results: int = Field(default=4)
    
    # Application
    log_level: str = Field(default="INFO")
    max_tokens: int = Field(default=2000)
    
    def validate_api_key(self) -> bool:
        """Validate OpenAI API key exists"""
        if not self.openai_api_key or self.openai_api_key == "your_openai_key_here":
            raise ValueError(
                "OPENAI_API_KEY not set in .env file. "
                "Get your key from: https://platform.openai.com/api-keys"
            )
        return True

# Global settings instance
settings = Settings()
