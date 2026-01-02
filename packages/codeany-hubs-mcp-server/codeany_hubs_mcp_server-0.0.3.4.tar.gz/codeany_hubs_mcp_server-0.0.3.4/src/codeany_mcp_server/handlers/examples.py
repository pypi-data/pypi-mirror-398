"""Handlers for sample input/output examples."""

from __future__ import annotations

from typing import Any, Dict, List, cast

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
    router.add_tool("tasks.examples.get", lambda p, prompt: _get_examples(guard, factory, p, prompt))
    router.add_tool(
        "tasks.examples.set",
        lambda p, prompt: _set_examples(guard, factory, config, p, prompt),
    )
    router.add_tool(
        "tasks.examples.add",
        lambda p, prompt: _add_example(guard, factory, config, p, prompt),
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


def _validate_examples_limit(config: MCPServerConfig, examples: List[Any]) -> None:
    if len(examples) > config.max_examples:
        raise ValueError(
            f"Example list exceeds maximum allowed count of {config.max_examples} entries.",
        )


def _get_examples(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.get_examples(hub=hub, task_id=task_id)
        return to_payload(result)


def _set_examples(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    config: MCPServerConfig,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.examples.set", hub=hub)

    inputs = params.get("inputs")
    outputs = params.get("outputs")
    if inputs is not None:
        _validate_examples_limit(config, list(inputs))
    if outputs is not None:
        _validate_examples_limit(config, list(outputs))

    with factory.build_sync_client(prompt) as client:
        result = client.tasks.set_examples(
            hub=hub,
            task_id=task_id,
            inputs=inputs,
            outputs=outputs,
        )
        return to_payload(result)


def _add_example(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    config: MCPServerConfig,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.examples.add", hub=hub)

    input_value: Any = require_param(params, "input")
    output_value: Any = require_param(params, "output")

    with factory.build_sync_client(prompt) as client:
        result = client.tasks.add_example(
            hub=hub,
            task_id=task_id,
            input_data=input_value,
            output_data=output_value,
        )
        return to_payload(result)


__all__ = ["register"]
