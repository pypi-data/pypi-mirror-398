"""Handlers for core task management operations."""

from __future__ import annotations

from typing import Any, Dict, Mapping, cast

from ..auth_guard import MCPAuthorizationGuard
from ..client_factory import ClientFactory
from ..config import MCPServerConfig
from ..router import Router
from ..types import ConsentPrompt
from ._utils import require_confirm, require_param, to_payload

_FILTER_PARAM_KEYS = (
    "query",
    "search",
    "visibility",
    "ordering",
    "type",
)


def register(
    router: Router,
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    config: MCPServerConfig,
) -> None:
    router.add_tool("tasks.create", lambda params, prompt: _create(guard, factory, params, prompt))
    router.add_tool("tasks.list", lambda params, prompt: _list_tasks(guard, factory, params, prompt))
    router.add_tool("tasks.delete", lambda params, prompt: _delete(guard, factory, params, prompt))
    router.add_tool("tasks.rename", lambda params, prompt: _rename(guard, factory, params, prompt))
    router.add_tool(
        "tasks.toggle_visibility",
        lambda params, prompt: _toggle_visibility(guard, factory, params, prompt),
    )
    router.add_tool(
        "tasks.get_settings",
        lambda params, prompt: _get_settings(guard, factory, params, prompt),
    )
    router.add_tool(
        "tasks.type.get",
        lambda params, prompt: _get_type(guard, factory, params, prompt),
    )
    router.add_tool(
        "tasks.type.update",
        lambda params, prompt: _update_type(guard, factory, params, prompt),
    )


def _call_task_method(
    factory: ClientFactory,
    prompt: ConsentPrompt,
    method_name: str,
    params: Dict[str, Any],
) -> Any:
    clean_params = {k: v for k, v in params.items() if k != "confirm"}
    with factory.build_sync_client(prompt) as client:
        method = getattr(client.tasks, method_name)
        result = method(**clean_params)
        return to_payload(result)


def _ensure_hub_access(guard: MCPAuthorizationGuard, params: Dict[str, Any], prompt: ConsentPrompt) -> str:
    guard.ensure_session_consent(prompt)
    hub = cast(str, require_param(params, "hub"))
    guard.ensure_hub_allowed(hub)
    return hub


def _create(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    _ensure_hub_access(guard, params, prompt)
    return _call_task_method(factory, prompt, "create", params)


def _delete(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub = _ensure_hub_access(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.delete", hub=hub)
    return _call_task_method(factory, prompt, "delete", params)


def _rename(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub = _ensure_hub_access(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.rename", hub=hub)
    return _call_task_method(factory, prompt, "rename", params)


def _toggle_visibility(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub = _ensure_hub_access(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.toggle_visibility", hub=hub)
    return _call_task_method(factory, prompt, "toggle_visibility", params)


def _get_settings(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    _ensure_hub_access(guard, params, prompt)
    return _call_task_method(factory, prompt, "get_settings", params)


def _list_tasks(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    """List tasks for a hub with optional pagination filters."""

    hub = _ensure_hub_access(guard, params, prompt)

    call_params: Dict[str, Any] = {"hub": hub}
    if params.get("page") is not None:
        call_params["page"] = params["page"]
    page_size = params.get("page_size")
    if page_size is None and params.get("pageSize") is not None:
        page_size = params["pageSize"]
    if page_size is not None:
        call_params["page_size"] = page_size

    filters = _extract_list_filters(params)
    if filters:
        call_params["filters"] = filters

    return _call_task_method(factory, prompt, "list", call_params)


def _extract_list_filters(params: Mapping[str, Any]) -> Dict[str, Any]:
    filters: Dict[str, Any] = {}

    raw_filters = params.get("filters")
    if raw_filters is not None:
        if not isinstance(raw_filters, Mapping):
            raise ValueError("Parameter 'filters' must be an object.")
        filters.update({k: v for k, v in raw_filters.items() if v is not None})

    for key in _FILTER_PARAM_KEYS:
        if key not in params:
            continue
        value = params[key]
        if value is None:
            continue
        filters[key] = value
    return filters


def _get_type(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    _ensure_hub_access(guard, params, prompt)
    return _call_task_method(factory, prompt, "get_type", params)


def _update_type(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub = _ensure_hub_access(guard, params, prompt)
    require_param(params, "payload")
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.type.update", hub=hub)
    return _call_task_method(factory, prompt, "update_type", params)


__all__ = ["register"]
