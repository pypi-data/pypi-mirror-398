"""Handlers for task execution limits."""

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
    router.add_tool("tasks.limits.get", lambda params, prompt: _get_limits(guard, factory, params, prompt))
    router.add_tool(
        "tasks.limits.update",
        lambda params, prompt: _update_limits(guard, factory, params, prompt),
    )


def _get_limits(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    guard.ensure_session_consent(prompt)
    hub = cast(str, require_param(params, "hub"))
    task_id = cast(str, require_param(params, "task_id"))
    guard.ensure_hub_allowed(hub)
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.get_limits(hub=hub, task_id=task_id)
        return to_payload(result)


def _update_limits(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    guard.ensure_session_consent(prompt)
    hub = cast(str, require_param(params, "hub"))
    task_id = cast(str, require_param(params, "task_id"))
    guard.ensure_hub_allowed(hub)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.limits.update", hub=hub)
    time_limit, memory_limit = _extract_limits(params)
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.update_limits(
            hub=hub,
            task_id=task_id,
            time_limit=time_limit,
            memory_limit=memory_limit,
        )
        return to_payload(result)


def _extract_limits(params: Dict[str, Any]) -> tuple[int, int]:
    merged: Dict[str, Any] = {}
    limits_block = params.get("limits")
    if limits_block is not None:
        if not isinstance(limits_block, Dict):
            raise ValueError("Parameter 'limits' must be an object.")
        merged.update(limits_block)
    if "time_limit" in params:
        merged["time_limit"] = params["time_limit"]
    if "memory_limit" in params:
        merged["memory_limit"] = params["memory_limit"]

    if "time_limit" not in merged or "memory_limit" not in merged:
        raise ValueError("Both 'time_limit' and 'memory_limit' must be provided.")

    try:
        time_limit = int(merged["time_limit"])
        memory_limit = int(merged["memory_limit"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Limits must be integers.") from exc

    if time_limit <= 0 or memory_limit <= 0:
        raise ValueError("Limits must be positive integers.")

    return time_limit, memory_limit


__all__ = ["register"]
