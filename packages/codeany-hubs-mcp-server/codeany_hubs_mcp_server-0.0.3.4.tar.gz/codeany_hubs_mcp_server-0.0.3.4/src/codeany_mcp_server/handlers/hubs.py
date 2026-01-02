"""Handlers for hub discovery endpoints."""

from __future__ import annotations

from typing import Any, Dict, cast

from ..auth_guard import MCPAuthorizationGuard
from ..client_factory import ClientFactory
from ..config import MCPServerConfig
from ..types import ConsentPrompt
from ..router import Router
from ._utils import require_param, to_payload, to_payload_list


def register(
    router: Router,
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    config: MCPServerConfig,
) -> None:
    router.add_tool("hubs.list_mine", lambda params, prompt: _list_mine(guard, factory, params, prompt))
    router.add_tool("hubs.detail", lambda params, prompt: _detail(guard, factory, params, prompt))


def _list_mine(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    guard.ensure_session_consent(prompt)
    with factory.build_sync_client(prompt) as client:
        return to_payload_list(client.hubs.list_mine())


def _detail(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub = cast(str, require_param(params, "hub"))
    guard.ensure_session_consent(prompt)
    guard.ensure_hub_allowed(hub)
    with factory.build_sync_client(prompt) as client:
        return to_payload(client.hubs.detail(hub))


__all__ = ["register"]
