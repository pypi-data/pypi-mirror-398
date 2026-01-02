"""Factory helpers to build SDK clients with per-request environment overlays."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager, contextmanager
from typing import (
    Any,
    AsyncContextManager,
    AsyncIterator,
    ContextManager,
    Dict,
    Iterator,
    Optional,
    cast,
    TYPE_CHECKING,
)

from .config import MCPServerConfig
from .logging_config import get_logger
from .types import ConsentPrompt

if TYPE_CHECKING:  # pragma: no cover
    from codeany_hub.client import AsyncCodeanyClient, CodeanyClient
    from codeany_hub.integrations.mcp import MCPClientBuilder as MCPClientBuilder
else:  # pragma: no cover
    try:
        from codeany_hub.client import AsyncCodeanyClient, CodeanyClient
        from codeany_hub.integrations.mcp import MCPClientBuilder
    except ImportError:
        AsyncCodeanyClient = Any
        CodeanyClient = Any

        class MCPClientBuilder:
            """Stubbed MCPClientBuilder for development without the SDK."""

            def build_sync_client(self, prompt: ConsentPrompt) -> Any:
                raise RuntimeError("MCPClientBuilder requires the CodeAny SDK.")

            async def build_async_client(self, prompt: ConsentPrompt) -> Any:
                raise RuntimeError("MCPClientBuilder requires the CodeAny SDK.")


@contextmanager
def _environment_overlay(updates: Dict[str, Optional[str]]) -> Iterator[None]:
    """Temporarily overrides environment variables."""

    original: Dict[str, Optional[str]] = {}
    try:
        for key, value in updates.items():
            original[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _maybe_close_client(client: Any) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        close()


async def _maybe_aclose_client(client: Any) -> None:
    aclose = getattr(client, "aclose", None)
    if callable(aclose):
        await aclose()


class ClientFactory:
    """Creates SDK clients with token-store and retry overrides."""

    def __init__(self, builder: MCPClientBuilder, config: MCPServerConfig) -> None:
        self._builder = builder
        self._config = config
        self._logger = get_logger("client_factory")

    def _env_updates(self) -> Dict[str, Optional[str]]:
        updates: Dict[str, Optional[str]] = {
            "CODEANY_RETRIES": str(self._config.retries),
            "CODEANY_RETRY_BACKOFF": str(self._config.retry_backoff),
            "CODEANY_LOG_REQUESTS": "1" if self._config.log_requests else "0",
        }

        if self._config.token_store_mode == "file":
            updates["CODEANY_TOKEN_STORE_MODE"] = "file"
            updates["CODEANY_TOKEN_STORE_PATH"] = self._config.token_store_path
        else:
            updates["CODEANY_TOKEN_STORE_MODE"] = "memory"
            updates["CODEANY_TOKEN_STORE_PATH"] = None

        return updates

    @staticmethod
    def _sanitize_env_for_log(key: str, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        upper = key.upper()
        if "PASSWORD" in upper:
            return "***"
        if "TOKEN_STORE" in upper:
            return value
        if "TOKEN" in upper or "SECRET" in upper:
            return f"{value[:4]}***" if len(value) > 4 else "***"
        return value

    @contextmanager
    def build_sync_client(self, prompt: ConsentPrompt) -> Iterator[CodeanyClient]:
        """Yield a configured synchronous CodeAny client."""

        env_updates = self._env_updates()
        logger = get_logger("client_factory")
        if self._config.verbose_logging:
            sanitized = {
                key: self._sanitize_env_for_log(key, value)
                for key, value in env_updates.items()
            }
            logger.info("Applying MCP environment overlay: %s", sanitized)
            logger.info(
                "Login context: hub=%s user=%s base_url=%s",
                os.environ.get("CODEANY_HUB"),
                os.environ.get("CODEANY_USERNAME"),
                os.environ.get("CODEANY_BASE_URL"),
            )
        with _environment_overlay(env_updates):
            built = self._builder.build_sync_client(prompt)
            if hasattr(built, "__enter__") and hasattr(built, "__exit__"):
                context_manager = cast(ContextManager[Any], built)
                with context_manager as managed_client:
                    self._ensure_token(managed_client)
                    yield managed_client
            else:
                try:
                    self._ensure_token(built)
                    yield built
                finally:
                    _maybe_close_client(built)

    @asynccontextmanager
    async def build_async_client(self, prompt: ConsentPrompt) -> AsyncIterator[AsyncCodeanyClient]:
        """Yield a configured asynchronous CodeAny client."""

        env_updates = self._env_updates()
        with _environment_overlay(env_updates):
            built = await self._builder.build_async_client(prompt)
            if hasattr(built, "__aenter__") and hasattr(built, "__aexit__"):
                async_context_manager = cast(AsyncContextManager[Any], built)
                async with async_context_manager as managed_client:
                    await self._ensure_async_token(managed_client)
                    yield managed_client
            else:
                try:
                    await self._ensure_async_token(built)
                    yield built
                finally:
                    await _maybe_aclose_client(built)

    def _ensure_token(self, client: Any) -> None:
        auth = getattr(client, "auth", None)
        if auth is None:
            return
        ensure = getattr(auth, "ensure_token", None)
        if callable(ensure):
            try:
                ensure()
                token = getattr(auth, "access_token", None)
                if token and self._config.verbose_logging:
                    masked = f"{token[:4]}***" if len(token) > 4 else "***"
                    self._logger.info("Token refreshed (sync): %s", masked)
            except Exception:
                self._logger.exception("Failed to ensure access token (sync)")

    async def _ensure_async_token(self, client: Any) -> None:
        auth = getattr(client, "auth", None)
        if auth is None:
            return
        ensure = getattr(auth, "ensure_token", None)
        if ensure is None:
            return
        try:
            result = ensure()
            if hasattr(result, "__await__"):
                await result
            token = getattr(auth, "access_token", None)
            if token and self._config.verbose_logging:
                masked = f"{token[:4]}***" if len(token) > 4 else "***"
                self._logger.info("Token refreshed (async): %s", masked)
        except Exception:
            self._logger.exception("Failed to ensure access token (async)")


__all__ = ["ClientFactory"]
