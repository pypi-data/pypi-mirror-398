"""Logging configuration helpers for the CodeAny Hub MCP server."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import MCPServerConfig

LOGGER_NAME = "codeany_mcp_server"


def configure_logging(config: MCPServerConfig) -> logging.Logger:
    """
    Configure application logging based on the MCP server configuration.

    A file handler is registered when `config.log_path` is provided. Logs default
    to INFO level unless overridden by `MCP_LOG_LEVEL`.
    """

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, config.log_level, logging.INFO))
    logger.propagate = False

    # Ensure we do not duplicate handlers across subsequent invocations.
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S"
        )

        # Always log warnings and above to stderr for operator visibility.
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.WARNING)
        stderr_handler.setFormatter(formatter)
        logger.addHandler(stderr_handler)

        if config.log_path:
            file_handler = _build_file_handler(config.log_path, formatter, config.log_level)
            logger.addHandler(file_handler)

    return logger


def _build_file_handler(path: str, formatter: logging.Formatter, level: str) -> logging.Handler:
    import tempfile
    
    expanded = Path(path).expanduser()
    if not expanded.is_absolute():
        expanded = (Path.cwd() / expanded).resolve()
    
    # Fallback paths in order of preference
    fallback_paths = [
        expanded,
        Path.cwd() / Path(path).name,
        Path(tempfile.gettempdir()) / Path(path).name,
    ]
    
    last_error: Exception | None = None
    for log_path in fallback_paths:
        try:
            if log_path.parent and not log_path.parent.exists():
                log_path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(log_path, encoding="utf-8")
            handler.setLevel(getattr(logging, level, logging.INFO))
            handler.setFormatter(formatter)
            return handler
        except (PermissionError, OSError) as exc:
            last_error = exc
            continue
    
    # If all paths fail, return a NullHandler and log a warning
    import sys
    print(f"Warning: Could not create log file at any location: {fallback_paths}. Error: {last_error}", file=sys.stderr)
    null_handler = logging.NullHandler()
    null_handler.setLevel(getattr(logging, level, logging.INFO))
    return null_handler


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Fetch a named logger within the MCP server namespace."""

    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return logging.getLogger(LOGGER_NAME)


__all__ = ["configure_logging", "get_logger", "LOGGER_NAME"]
