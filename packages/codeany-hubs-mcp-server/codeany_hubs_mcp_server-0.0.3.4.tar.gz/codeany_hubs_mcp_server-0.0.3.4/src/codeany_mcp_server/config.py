"""Configuration management for the CodeAny Hub MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Optional, Set
import logging
import tempfile

EnvMapping = Mapping[str, str]


def _parse_bool(value: str, *, default: bool) -> bool:
    truthy = {"1", "true", "yes", "y", "on"}
    falsy = {"0", "false", "no", "n", "off"}
    lowered = value.strip().lower()
    if lowered in truthy:
        return True
    if lowered in falsy:
        return False
    return default


def _parse_int(value: str, *, default: int) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer value: {value}") from exc


def _parse_float(value: str, *, default: float) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid float value: {value}") from exc


def _parse_allowlist(value: str) -> Optional[Set[str]]:
    if not value:
        return None
    lowered = value.strip().lower()
    if lowered == "none":
        return None
    items = {item.strip() for item in value.split(",") if item.strip() and item.strip().lower() != "none"}
    return items or None


def _build_destructive_message_provider(template: str) -> Callable[[str, str], str]:
    def _template(op_name: str, hub: str) -> str:
        return template.format(op_name=op_name, hub=hub)

    return _template


def _parse_log_level(value: str, *, default: str) -> str:
    allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
    upper = value.strip().upper()
    if upper not in allowed:
        raise ValueError(f"Invalid MCP_LOG_LEVEL '{value}'. Choose from {sorted(allowed)}.")
    return upper


@dataclass(slots=True)
class MCPServerConfig:
    """Configuration options for the MCP server."""

    ask_on_start: bool = True
    ask_on_destructive_ops: bool = True
    token_store_mode: str = "file"
    token_store_path: Optional[str] = None
    hub_allowlist: Optional[Set[str]] = None
    retries: int = 2
    retry_backoff: float = 0.3
    log_requests: bool = False
    verbose_logging: bool = False
    max_upload_mb: int = 25
    max_examples: int = 50
    allow_local_paths: bool = False
    consent_message: Optional[str] = None
    destructive_message_provider: Optional[Callable[[str, str], str]] = None
    log_path: Optional[str] = "codeany-hub-mcp.log"
    log_level: str = "INFO"


def load_from_env(env: Optional[EnvMapping] = None) -> MCPServerConfig:
    """Load configuration values from the environment."""

    environ: EnvMapping = os.environ if env is None else env
    cfg = MCPServerConfig()
    logger = logging.getLogger("codeany_mcp_server.config")

    if "MCP_ASK_ON_START" in environ:
        cfg.ask_on_start = _parse_bool(environ["MCP_ASK_ON_START"], default=cfg.ask_on_start)
    if "MCP_ASK_ON_DESTRUCTIVE_OPS" in environ:
        cfg.ask_on_destructive_ops = _parse_bool(
            environ["MCP_ASK_ON_DESTRUCTIVE_OPS"], default=cfg.ask_on_destructive_ops
        )

    if "MCP_TOKEN_STORE_MODE" in environ:
        mode = environ["MCP_TOKEN_STORE_MODE"].strip().lower()
        if mode not in {"memory", "file"}:
            raise ValueError("MCP_TOKEN_STORE_MODE must be either 'memory' or 'file'")
        cfg.token_store_mode = mode
    if "MCP_TOKEN_STORE_PATH" in environ:
        path_value = environ["MCP_TOKEN_STORE_PATH"].strip()
        if not path_value or path_value.lower() == "none":
            cfg.token_store_path = None
        else:
            cfg.token_store_path = str(_normalize_token_path(path_value))

    if "MCP_HUB_ALLOWLIST" in environ:
        cfg.hub_allowlist = _parse_allowlist(environ["MCP_HUB_ALLOWLIST"])

    if "MCP_RETRIES" in environ:
        cfg.retries = _parse_int(environ["MCP_RETRIES"], default=cfg.retries)
    if "MCP_RETRY_BACKOFF" in environ:
        cfg.retry_backoff = _parse_float(environ["MCP_RETRY_BACKOFF"], default=cfg.retry_backoff)
    if "MCP_LOG_REQUESTS" in environ:
        cfg.log_requests = _parse_bool(environ["MCP_LOG_REQUESTS"], default=cfg.log_requests)
    if "MCP_VERBOSE_LOGGING" in environ:
        cfg.verbose_logging = _parse_bool(environ["MCP_VERBOSE_LOGGING"], default=cfg.verbose_logging)

    if "MCP_MAX_UPLOAD_MB" in environ:
        cfg.max_upload_mb = _parse_int(environ["MCP_MAX_UPLOAD_MB"], default=cfg.max_upload_mb)
    if "MCP_MAX_EXAMPLES" in environ:
        cfg.max_examples = _parse_int(environ["MCP_MAX_EXAMPLES"], default=cfg.max_examples)
    if "MCP_ALLOW_LOCAL_PATHS" in environ:
        cfg.allow_local_paths = _parse_bool(environ["MCP_ALLOW_LOCAL_PATHS"], default=cfg.allow_local_paths)

    if "MCP_CONSENT_MESSAGE" in environ:
        cfg.consent_message = environ["MCP_CONSENT_MESSAGE"]
    if "MCP_DESTRUCTIVE_MESSAGE_TEMPLATE" in environ:
        template = environ["MCP_DESTRUCTIVE_MESSAGE_TEMPLATE"]
        cfg.destructive_message_provider = _build_destructive_message_provider(template)
    if "MCP_LOG_PATH" in environ:
        path_value = environ["MCP_LOG_PATH"].strip()
        cfg.log_path = None if path_value.lower() == "none" else path_value or None
    if "MCP_LOG_LEVEL" in environ:
        cfg.log_level = _parse_log_level(environ["MCP_LOG_LEVEL"], default=cfg.log_level)

    if cfg.token_store_mode == "file":
        if cfg.token_store_path:
            cfg.token_store_path = str(_ensure_token_path(cfg.token_store_path, logger))
        else:
            default_path = Path.home() / ".codeany" / "mcp_tokens.json"
            cfg.token_store_path = str(_ensure_token_path(default_path, logger))
        logger.debug("Token store configured at %s", cfg.token_store_path)

    return cfg


def _normalize_token_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def _ensure_token_path(raw_path: str | Path, logger: logging.Logger) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as exc:
        # Fallbacks: try CWD, then try temp dir
        fallbacks = [
            Path.cwd() / "mcp_tokens.json",
            Path(tempfile.gettempdir()) / "codeany_mcp_tokens.json",
        ]
        
        for fb in fallbacks:
            if fb != path:
                logger.warning(
                    "Could not access token store at %s: %s. Falling back to %s", 
                    path, exc, fb
                )
                return _ensure_token_path(fb, logger)

        # If all fallbacks fail (or match original path which failed)
        raise PermissionError(
            f"Unable to create token store at {path}. "
            f"Tried fallbacks: {fallbacks}. "
            "Set MCP_TOKEN_STORE_PATH to a writable location."
        ) from exc

    if not path.exists():
        try:
            path.touch()
            logger.debug("Created token store file at %s", path)
        except (PermissionError, OSError) as exc:
            # Fallbacks: try CWD, then try temp dir
            fallbacks = [
                Path.cwd() / "mcp_tokens.json",
                Path(tempfile.gettempdir()) / "codeany_mcp_tokens.json",
            ]
            
            for fb in fallbacks:
                if fb != path:
                    logger.warning(
                        "Could not create token store at %s: %s. Falling back to %s", 
                        path, exc, fb
                    )
                    return _ensure_token_path(fb, logger)

            raise PermissionError(
                f"Unable to create token store at {path}. "
                f"Tried fallbacks: {fallbacks}. "
                "Set MCP_TOKEN_STORE_PATH to a writable location."
            ) from exc
    return path


__all__ = ["MCPServerConfig", "load_from_env"]
