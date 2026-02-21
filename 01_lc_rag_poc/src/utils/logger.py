"""
Logging Utilities
Purpose: Consistent logging across modules
"""

import sys
from loguru import logger
from .config import settings

# Remove default handler
logger.remove()

# Add custom handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level
)

# Add file handler
logger.add(
    "logs/rag_poc_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG"
)

def get_logger(name: str):
    """Get logger instance for module"""
    return logger.bind(name=name)
