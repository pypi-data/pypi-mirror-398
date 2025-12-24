"""Logging configuration for Keyword Generation"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None,
    enable_file_logging: bool = False,
    log_file: str = "keyword_generation.log",
) -> None:
    """
    Set up logging configuration for Keyword Generation
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Defaults to INFO if not provided
        format_string: Custom log format string
        enable_file_logging: Whether to log to file
        log_file: Path to log file (if enable_file_logging=True)
    """
    # Determine log level
    if level is None:
        level = logging.INFO
    else:
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Default format
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(funcName)s:%(lineno)d - %(message)s"
        )
    
    # Configure root logger for pipeline module (parent of all pipeline.* loggers)
    root_logger = logging.getLogger("pipeline")
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if enable_file_logging:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(format_string)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            root_logger.info(f"File logging enabled: {log_file}")
        except Exception as e:
            root_logger.warning(f"Failed to enable file logging: {e}")
    
    # Set levels for related modules (child loggers will inherit from pipeline)
    logging.getLogger("pipeline.integrations.seranking").setLevel(level)
    logging.getLogger("pipeline.keyword_generation").setLevel(level)
    
    root_logger.info(f"Logging configured: level={logging.getLevelName(level)}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration: float,
    details: Optional[dict] = None,
) -> None:
    """
    Log performance metrics
    
    Args:
        logger: Logger instance
        operation: Operation name
        duration: Duration in seconds
        details: Additional details to log
    """
    message = f"PERF: {operation} took {duration:.2f}s"
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        message += f" ({detail_str})"
    logger.info(message)


def log_api_call(
    logger: logging.Logger,
    api_name: str,
    endpoint: str,
    status: str = "success",
    duration: Optional[float] = None,
    error: Optional[Exception] = None,
) -> None:
    """
    Log API call details
    
    Args:
        logger: Logger instance
        api_name: API name (e.g., "Gemini", "SE Ranking")
        endpoint: Endpoint or operation name
        status: Status ("success", "failure", "retry")
        duration: Call duration in seconds
        error: Exception if call failed
    """
    message = f"API: {api_name} - {endpoint} - {status}"
    if duration is not None:
        message += f" ({duration:.2f}s)"
    if error:
        message += f" - Error: {error}"
    
    if status == "success":
        logger.debug(message)
    elif status == "retry":
        logger.warning(message)
    else:
        logger.error(message, exc_info=error is not None)

