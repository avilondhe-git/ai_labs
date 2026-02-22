"""
Logging Setup for Azure AI Agent POC
Purpose: Structured logging with Application Insights integration
"""

from loguru import logger
import sys
from typing import Optional
from config.config import settings


def setup_logger(app_insights_conn_str: Optional[str] = None) -> logger:
    """
    Configure structured logging
    
    WHY: loguru provides:
         - Colored console output (better DX)
         - Automatic rotation (prevents large log files)
         - Context preservation (trace errors easily)
         - Zero configuration (works out of box)
    
    Args:
        app_insights_conn_str: Optional Application Insights connection string
        
    Returns:
        Configured logger instance
    """
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # Add file handler with rotation
    logger.add(
        "logs/agent_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    # Application Insights integration (if configured)
    if app_insights_conn_str or settings.appinsights_connection_string:
        try:
            from opencensus.ext.azure.log_exporter import AzureLogHandler
            
            conn_str = app_insights_conn_str or settings.appinsights_connection_string
            logger.add(
                AzureLogHandler(connection_string=conn_str),
                level="INFO"
            )
            logger.info("✓ Application Insights logging enabled")
            
        except ImportError:
            logger.warning("⚠️  opencensus-ext-azure not installed. Skipping Application Insights integration.")
    
    logger.info("Logger initialized")
    return logger


# Create global logger instance
app_logger = setup_logger()
