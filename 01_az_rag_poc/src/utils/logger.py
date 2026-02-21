"""Application logging configuration"""

import sys
from loguru import logger
from src.utils.config import settings


def get_logger(name: str):
    """Get configured logger"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level
    )
    return logger.bind(name=name)
