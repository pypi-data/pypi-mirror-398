"""Logging infrastructure for planecompose.

Provides structured logging with rich output and file rotation.
"""
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler


# Global logger instance
_logger: logging.Logger | None = None


def setup_logger(
    verbose: bool = False,
    log_file: Path | None = None,
    name: str = "planecompose",
) -> logging.Logger:
    """
    Setup application logger with rich console output and optional file logging.
    
    Args:
        verbose: Enable debug logging
        log_file: Path to log file (enables file logging)
        name: Logger name
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logger(verbose=True)
        >>> logger.info("Starting operation")
        >>> logger.debug("Detailed debug info")
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with rich formatting
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=False,
        show_path=False if not verbose else True,
    )
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)
    
    # File handler with rotation (if log_file specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """
    Get the current logger instance.
    
    Returns:
        Logger instance (creates with defaults if not setup)
    """
    global _logger
    
    if _logger is None:
        _logger = setup_logger()
    
    return _logger


def reset_logger():
    """Reset the global logger instance (useful for testing)."""
    global _logger
    _logger = None

