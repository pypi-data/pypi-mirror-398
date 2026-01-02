"""Entry point for the CodeAny Hub MCP server (Content-Length framed JSON-RPC)."""

from __future__ import annotations

import sys
import os
from typing import Any, TYPE_CHECKING

from .auth_guard import MCPAuthorizationGuard
from .client_factory import ClientFactory
from .config import MCPServerConfig, load_from_env
from .handlers import register_all
from .logging_config import configure_logging
from .router import Router
from .types import ConsentPrompt

if TYPE_CHECKING:  # pragma: no cover
    from codeany_hub.integrations.mcp import MCPClientBuilder as _MCPClientBuilder
else:  # pragma: no cover
    try:
        from codeany_hub.integrations.mcp import MCPClientBuilder as _MCPClientBuilder
    except ImportError:

        class _MCPClientBuilder:
            """Stub used when the SDK is unavailable."""

            def build_sync_client(self, prompt: ConsentPrompt) -> Any:
                raise RuntimeError("Install codeany-hub to run the MCP server.")

            async def build_async_client(self, prompt: ConsentPrompt) -> Any:
                raise RuntimeError("Install codeany-hub to run the MCP server.")


def main() -> int:
    """Launch the MCP server using Content-Length framed stdio."""

    config: MCPServerConfig = load_from_env()
    logger = configure_logging(config)
    builder = _MCPClientBuilder()
    guard = MCPAuthorizationGuard(config)
    factory = ClientFactory(builder, config)
    router = Router()
    register_all(router, guard, factory, config)
    if config.verbose_logging:
        sys.stderr.write(f"[codeany-hub-mcp] Registered tools: {sorted(router.list_tools())}\n")
        interesting_env = {}
        for key, value in sorted(os.environ.items()):
            if key.startswith(("CODEANY_", "MCP_")):
                if any(secret in key for secret in ("PASSWORD", "TOKEN", "SECRET")):
                    interesting_env[key] = "***"
                else:
                    interesting_env[key] = value
        sys.stderr.write(f"[codeany-hub-mcp] Effective environment: {interesting_env}\n")
        sys.stderr.flush()

    log_location = config.log_path or "stderr"
    logger.info("CodeAny Hub MCP server starting (logs at %s)", log_location)
    sys.stderr.write(f"[codeany-hub-mcp] Server ready. Logging to {log_location}.\n")
    sys.stderr.flush()

    return router.run_stdio()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
