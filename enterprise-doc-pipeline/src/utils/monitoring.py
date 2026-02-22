import logging
from typing import Dict, Any
from datetime import datetime


def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('document_processing.log')
        ]
    )


def log_metric(metric_name: str, value: float, properties: Dict[str, Any] = None):
    """Log a custom metric"""
    logger = logging.getLogger(__name__)
    metric_data = {
        "metric": metric_name,
        "value": value,
        "timestamp": datetime.utcnow().isoformat(),
        "properties": properties or {}
    }
    logger.info(f"METRIC: {metric_data}")


def log_event(event_name: str, properties: Dict[str, Any] = None):
    """Log a custom event"""
    logger = logging.getLogger(__name__)
    event_data = {
        "event": event_name,
        "timestamp": datetime.utcnow().isoformat(),
        "properties": properties or {}
    }
    logger.info(f"EVENT: {event_data}")


def log_exception(exception: Exception, context: Dict[str, Any] = None):
    """Log an exception with context"""
    logger = logging.getLogger(__name__)
    exception_data = {
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
        "timestamp": datetime.utcnow().isoformat(),
        "context": context or {}
    }
    logger.error(f"EXCEPTION: {exception_data}", exc_info=True)
