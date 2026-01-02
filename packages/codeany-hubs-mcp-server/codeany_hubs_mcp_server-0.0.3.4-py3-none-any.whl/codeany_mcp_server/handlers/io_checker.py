"""Handlers for IO/checker configuration."""

from __future__ import annotations

from typing import Any, Dict, cast

from ..auth_guard import MCPAuthorizationGuard
from ..client_factory import ClientFactory
from ..config import MCPServerConfig
from ..router import Router
from ..types import ConsentPrompt
from ._utils import require_confirm, require_param, to_payload


def register(
    router: Router,
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    config: MCPServerConfig,
) -> None:
    router.add_tool("tasks.io.get", lambda params, prompt: _get_io(guard, factory, params, prompt))
    router.add_tool("tasks.io.update", lambda params, prompt: _update_io(guard, factory, params, prompt))
    router.add_tool("tasks.checker.get", lambda params, prompt: _get_checker(guard, factory, params, prompt))
    router.add_tool(
        "tasks.checker.update",
        lambda params, prompt: _update_checker(guard, factory, params, prompt),
    )


def _ensure_context(
    guard: MCPAuthorizationGuard,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> tuple[str, str]:
    guard.ensure_session_consent(prompt)
    hub = cast(str, require_param(params, "hub"))
    task_id = cast(str, require_param(params, "task_id"))
    guard.ensure_hub_allowed(hub)
    return hub, task_id


def _get_io(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.get_io(hub=hub, task_id=task_id)
        return to_payload(result)


def _update_io(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.io.update", hub=hub)
    payload = cast(Dict[str, Any], require_param(params, "io"))
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.update_io(hub=hub, task_id=task_id, io=payload)
        return to_payload(result)


def _get_checker(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.get_checker(hub=hub, task_id=task_id)
        return to_payload(result)


def _update_checker(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    payload = cast(Dict[str, Any], require_param(params, "checker"))
    if "checker_type" not in payload:
        raise ValueError("checker_type is required to update the checker.")
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.checker.update", hub=hub)
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.update_checker(hub=hub, task_id=task_id, payload=payload)
        return to_payload(result)


__all__ = ["register"]
