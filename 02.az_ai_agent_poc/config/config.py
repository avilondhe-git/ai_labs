"""
Configuration Management for Azure AI Agent POC
Purpose: Centralized settings using environment variables
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    
    WHY: pydantic-settings provides:
         - Type validation (catches errors early)
         - Default values (simplifies setup)
         - .env file loading (local development)
         - IDE autocomplete (better DX)
    """
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = Field(
        ...,
        description="Azure OpenAI endpoint URL"
    )
    azure_openai_api_key: str = Field(
        ...,
        description="Azure OpenAI API key"
    )
    azure_openai_deployment: str = Field(
        "gpt-4o-mini",
        description="Deployment name (model)"
    )
    azure_openai_api_version: str = Field(
        "2024-02-01",
        description="API version"
    )
    
    # Azure Cosmos DB Configuration
    cosmos_endpoint: str = Field(
        ...,
        description="Cosmos DB endpoint URL"
    )
    cosmos_key: str = Field(
        ...,
        description="Cosmos DB master key"
    )
    cosmos_database: str = Field(
        "agent-db",
        description="Database name"
    )
    cosmos_container: str = Field(
        "conversations",
        description="Container name for conversation history"
    )
    
    # Tool API Keys
    tavily_api_key: Optional[str] = Field(
        None,
        description="Tavily API key for web search (optional)"
    )
    sendgrid_api_key: Optional[str] = Field(
        None,
        description="SendGrid API key for email (optional)"
    )
    
    # Application Insights (optional)
    appinsights_connection_string: Optional[str] = Field(
        None,
        description="Application Insights connection string"
    )
    
    # Application Settings
    log_level: str = Field(
        "INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create global settings instance
settings = Settings()
