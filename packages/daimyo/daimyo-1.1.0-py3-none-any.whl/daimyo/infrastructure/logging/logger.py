"""Logging infrastructure using loguru."""

import sys
from pathlib import Path

from loguru import logger

from daimyo.config import settings


def setup_logging() -> None:
    """Configure loguru with multiple sinks.

    - Console output (human-readable, colored)
    - File output (human-readable)
    - JSONL output (machine-readable)

    :rtype: None
    """
    logger.remove()

    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=settings.CONSOLE_LOG_LEVEL,
        colorize=True,
    )

    log_file_path = Path(settings.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        settings.LOG_FILE,
        rotation="10 MB",
        retention="1 week",
        level=settings.FILE_LOG_LEVEL,
        format=("{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"),
        colorize=False,
    )

    json_log_path = Path(settings.LOG_JSON_FILE)
    json_log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        settings.LOG_JSON_FILE,
        serialize=True,
        rotation="10 MB",
        retention="1 week",
        level=settings.FILE_LOG_LEVEL,
    )

    logger.info(
        f"Logging initialized (console: {settings.CONSOLE_LOG_LEVEL}, "
        f"file: {settings.FILE_LOG_LEVEL})"
    )


def get_logger(name: str):
    """Get a logger instance for a module.

    :param name: Module name (typically __name__)
    :type name: str
    :returns: Logger instance bound to the module name
    """
    return logger.bind(module=name)


__all__ = ["setup_logging", "get_logger", "logger"]
