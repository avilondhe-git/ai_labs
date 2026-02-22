from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration using Pydantic"""
    
    AZURE_STORAGE_CONNECTION_STRING: str
    BLOB_CONTAINER_NAME: str = "documents"
    
    DOCUMENT_INTELLIGENCE_ENDPOINT: str
    DOCUMENT_INTELLIGENCE_KEY: Optional[str] = None
    
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-ada-002"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    
    COSMOS_ENDPOINT: str
    COSMOS_KEY: Optional[str] = None
    COSMOS_DATABASE_NAME: str = "document-processing"
    COSMOS_CONTAINER_NAME: str = "documents"
    
    SEARCH_ENDPOINT: str
    SEARCH_API_KEY: Optional[str] = None
    SEARCH_INDEX_NAME: str = "documents-index"
    
    APPINSIGHTS_CONNECTION_STRING: str
    
    MAX_PARALLEL_DOCUMENTS: int = 10
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
