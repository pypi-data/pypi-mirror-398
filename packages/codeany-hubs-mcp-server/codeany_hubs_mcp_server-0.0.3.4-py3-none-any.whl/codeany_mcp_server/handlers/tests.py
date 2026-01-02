"""Handlers for individual test case management."""

from __future__ import annotations

from typing import Any, Dict, cast

from ..auth_guard import MCPAuthorizationGuard
from ..client_factory import ClientFactory
from ..config import MCPServerConfig
from ..io_utils import coerce_bytes_or_path, enforce_size_limit
from ..router import Router
from ..types import ConsentPrompt
from ._utils import require_confirm, require_param, to_payload


def register(
    router: Router,
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    config: MCPServerConfig,
) -> None:
    router.add_tool("tasks.tests.get", lambda p, prompt: _get_testcase(guard, factory, p, prompt))
    router.add_tool(
        "tasks.tests.upload_single",
        lambda p, prompt: _upload_single(guard, factory, config, p, prompt),
    )
    router.add_tool("tasks.tests.delete_one", lambda p, prompt: _delete_one(guard, factory, p, prompt))
    router.add_tool("tasks.tests.delete_many", lambda p, prompt: _delete_many(guard, factory, p, prompt))


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


def _get_testcase(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    testset_id = cast(str, require_param(params, "testset_id"))
    index = cast(int, require_param(params, "index"))
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.get_testcase(
            hub=hub,
            task_id=task_id,
            testset_id=testset_id,
            index=index,
        )
        return to_payload(result)


def _upload_single(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    config: MCPServerConfig,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.tests.upload_single", hub=hub)

    testset_id = cast(str, require_param(params, "testset_id"))
    input_payload: Any = require_param(params, "input_data")
    answer_payload: Any = require_param(params, "answer_data")
    position = params.get("position", -1)

    input_bytes = coerce_bytes_or_path(input_payload, allow_paths=config.allow_local_paths)
    answer_bytes = coerce_bytes_or_path(answer_payload, allow_paths=config.allow_local_paths)
    enforce_size_limit(input_bytes, config.max_upload_mb)
    enforce_size_limit(answer_bytes, config.max_upload_mb)

    with factory.build_sync_client(prompt) as client:
        client.tasks.upload_single_test(
            hub=hub,
            task_id=task_id,
            testset_id=testset_id,
            input_path=input_bytes,
            answer_path=answer_bytes,
            pos=position,
        )
        return {"status": "uploaded"}


def _delete_one(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.tests.delete_one", hub=hub)

    testset_id = cast(str, require_param(params, "testset_id"))
    index = cast(int, require_param(params, "index"))

    with factory.build_sync_client(prompt) as client:
        result = client.tasks.delete_testcase(
            hub=hub,
            task_id=task_id,
            testset_id=testset_id,
            index=index,
        )
        return to_payload(result)


def _delete_many(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.tests.delete_many", hub=hub)

    testset_id = cast(str, require_param(params, "testset_id"))
    indexes = cast(list[int], require_param(params, "indexes"))

    with factory.build_sync_client(prompt) as client:
        result = client.tasks.delete_testcases(
            hub=hub,
            task_id=task_id,
            testset_id=testset_id,
            indexes=indexes,
        )
        return to_payload(result)


__all__ = ["register"]
