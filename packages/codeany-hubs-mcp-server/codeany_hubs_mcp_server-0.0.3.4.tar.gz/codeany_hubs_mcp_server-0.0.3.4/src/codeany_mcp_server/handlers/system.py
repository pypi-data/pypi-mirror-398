"""System-level MCP handlers (initialize, ping, etc.)."""

from __future__ import annotations

from importlib import metadata
from typing import Any, Dict

from ..auth_guard import MCPAuthorizationGuard
from ..client_factory import ClientFactory
from ..config import MCPServerConfig
from ..router import Router
from .capabilities import get_tool_details


def register(
    router: Router,
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    config: MCPServerConfig,
) -> None:
    router.add_tool(
        "initialize",
        lambda params, prompt: _initialize_handler(config, params),
    )
    router.add_tool(
        "ping",
        lambda params, prompt: _ping_handler(),
    )


def _initialize_handler(config: MCPServerConfig, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Spec-compliant initialize result.

    Required:
      - protocolVersion
      - capabilities
      - serverInfo

    Extras (for broader client compatibility and our tests):
      - serverCapabilities (alias of capabilities)
      - tools (full definitions)
      - toolNames (flat names)
    """
    requested = None
    try:
        requested = params.get("protocolVersion")
    except Exception:
        requested = None

    # Echo requested version if provided; otherwise default to the widely used spec revision.
    protocol_version = requested or "2024-11-05"

    capabilities: Dict[str, Any] = {
        "logging": {},
        "prompts": {},
        "resources": {},
        "tools": {},
    }

    tool_details = get_tool_details()
    initialize_tools: list[Dict[str, Any]] = []
    for tool in tool_details:
        metadata = dict(tool.get("metadata", {}))
        metadata.setdefault("sanitized", tool["name"])
        initialize_tools.append(
            {
                **tool,
                "name": metadata.get("original", tool["name"]),
                "metadata": metadata,
            }
        )

    return {
        "protocolVersion": protocol_version,
        "capabilities": capabilities,
        "serverCapabilities": capabilities,
        "serverInfo": {
            "name": "codeany-hub-mcp-server",
            "version": _server_version(),
        },
        "tools": initialize_tools,
        "toolNames": [tool["name"] for tool in tool_details],
    }


def _ping_handler() -> Dict[str, Any]:
    return {"ok": True}


def _server_version() -> str:
    try:
        return metadata.version("codeany-hub-mcp-server")
    except metadata.PackageNotFoundError:
        return "0.1.0"


__all__ = ["register"]
