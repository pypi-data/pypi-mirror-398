"""
Structured logging configuration for StackWeaver.

Provides console and file logging with:
- Rich console formatting
- File output with rotation
- Configurable log levels
- Sensitive data redaction
"""

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

# Sensitive patterns to redact
SENSITIVE_PATTERNS = [
    (
        re.compile(r"(api[_\-\s]?key['\"]?\s*[:=]\s*['\"]?)(\S+)", re.IGNORECASE),
        r"\1***REDACTED***",
    ),
    (re.compile(r"(password['\"]?\s*[:=]\s*['\"]?)(\S+)", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(token['\"]?\s*[:=]\s*['\"]?)(\S+)", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(secret['\"]?\s*[:=]\s*['\"]?)(\S+)", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(bearer\s+)([a-zA-Z0-9_\-\.]+)", re.IGNORECASE), r"\1***REDACTED***"),
]


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive data from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Redact sensitive information from log message.

        Args:
            record: Log record to filter

        Returns:
            Always True (record is not filtered out, just modified)
        """
        # Redact message
        message = record.getMessage()
        for pattern, replacement in SENSITIVE_PATTERNS:
            message = pattern.sub(replacement, message)

        # Update record with redacted message
        record.msg = message
        record.args = ()

        return True


def get_log_level() -> str:
    """
    Get log level from environment variable.

    Returns:
        Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    return os.environ.get("STACKWEAVER_LOG_LEVEL", "INFO").upper()


def get_log_dir() -> Path:
    """
    Get log directory path.

    Returns:
        Path to ~/.stackweaver/logs/
    """
    log_dir = Path.home() / ".stackweaver" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging(console_output: bool = True, file_output: bool = True) -> None:
    """
    Configure logging for StackWeaver.

    Sets up:
    - Rich console handler with colored output
    - Rotating file handler (7 days retention)
    - Sensitive data redaction

    Args:
        console_output: Whether to enable console logging
        file_output: Whether to enable file logging
    """
    # Get log level
    log_level_str = get_log_level()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers = []

    # Create sensitive data filter
    sensitive_filter = SensitiveDataFilter()

    # Console handler (Rich)
    if console_output:
        console = Console()
        console_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
            markup=True,
        )
        console_handler.setLevel(log_level)
        console_handler.addFilter(sensitive_filter)
        root_logger.addHandler(console_handler)

    # File handler (Rotating)
    if file_output:
        log_dir = get_log_dir()
        log_file = log_dir / "stackweaver.log"

        # 10MB per file, keep 7 backups (roughly 7 days)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.addFilter(sensitive_filter)

        # File formatter (structured)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Log initial setup
    logger = logging.getLogger(__name__)
    logger.debug(
        f"Logging configured: level={log_level_str}, console={console_output}, file={file_output}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Configure logging on module import
setup_logging()
