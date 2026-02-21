"""Application configuration from environment variables"""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    # Azure Storage
    azure_storage_connection_string: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    azure_storage_container_name: str = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "documents")

    # Azure OpenAI
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    azure_openai_embedding_deployment: str = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
    azure_openai_chat_deployment: str = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")

    # Azure AI Search
    azure_search_endpoint: str = os.getenv("AZURE_SEARCH_ENDPOINT")
    azure_search_admin_key: str = os.getenv("AZURE_SEARCH_ADMIN_KEY")
    azure_search_index_name: str = os.getenv("AZURE_SEARCH_INDEX_NAME", "documents-index")

    # Configuration
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    top_k_results: int = int(os.getenv("TOP_K_RESULTS", "4"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
