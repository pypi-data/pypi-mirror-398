"""Handlers for Multiple Choice Question (MCQ) task configuration."""

from __future__ import annotations

from typing import Any, Dict, Tuple, Union, cast

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
    router.add_tool("tasks.mcq.get_config", lambda p, prompt: _get_config(guard, factory, p, prompt))
    router.add_tool(
        "tasks.mcq.replace_config",
        lambda p, prompt: _replace_config(guard, factory, p, prompt),
    )
    router.add_tool(
        "tasks.mcq.patch_config",
        lambda p, prompt: _patch_config(guard, factory, p, prompt),
    )
    router.add_tool(
        "tasks.mcq.set_correct",
        lambda p, prompt: _set_correct(guard, factory, p, prompt),
    )


TaskId = Union[int, str]


def _ensure_context(
    guard: MCPAuthorizationGuard,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Tuple[str, TaskId]:
    guard.ensure_session_consent(prompt)
    hub = cast(str, require_param(params, "hub"))
    task_id = require_param(params, "task_id")
    guard.ensure_hub_allowed(hub)
    return hub, task_id


def _call_mcq_method(
    factory: ClientFactory,
    prompt: ConsentPrompt,
    method_name: str,
    **kwargs: Any,
) -> Any:
    with factory.build_sync_client(prompt) as client:
        hubs_service = getattr(client, "hubs", None)
        if hubs_service is None:
            raise RuntimeError("CodeAny client missing 'hubs' attribute required for MCQ tools.")
        mcq_service = getattr(hubs_service, "mcq", None)
        if mcq_service is None:
            raise RuntimeError("CodeAny SDK version does not expose 'hubs.mcq'; please upgrade.")
        method = getattr(mcq_service, method_name)
        result = method(**kwargs)
        return to_payload(result)


def _get_config(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    return _call_mcq_method(factory, prompt, "get_config", hub=hub, task_id=task_id)


def _replace_config(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    config_payload = require_param(params, "config")
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.mcq.replace_config", hub=hub)
    return _call_mcq_method(
        factory,
        prompt,
        "replace_config",
        hub=hub,
        task_id=task_id,
        config=config_payload,
    )


def _patch_config(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    patch_payload = require_param(params, "patch")
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.mcq.patch_config", hub=hub)
    return _call_mcq_method(
        factory,
        prompt,
        "patch_config",
        hub=hub,
        task_id=task_id,
        patch=patch_payload,
    )


def _set_correct(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    option_ids = require_param(params, "correct_option_ids")
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.mcq.set_correct", hub=hub)
    return _call_mcq_method(
        factory,
        prompt,
        "set_correct",
        hub=hub,
        task_id=task_id,
        correct_option_ids=option_ids,
    )
__all__ = ["register"]
