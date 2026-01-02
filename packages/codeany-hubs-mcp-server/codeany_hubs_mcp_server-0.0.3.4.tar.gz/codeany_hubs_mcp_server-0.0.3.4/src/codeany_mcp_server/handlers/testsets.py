"""Handlers for task testset management."""

from __future__ import annotations

from typing import Any, Dict, Iterator, cast

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
    router.add_tool("tasks.testsets.list", lambda p, prompt: _list_testsets(guard, factory, p, prompt))
    router.add_tool("tasks.testsets.get", lambda p, prompt: _get_testset(guard, factory, p, prompt))
    router.add_tool("tasks.testsets.create", lambda p, prompt: _create_testset(guard, factory, p, prompt))
    router.add_tool("tasks.testsets.update", lambda p, prompt: _update_testset(guard, factory, p, prompt))
    router.add_tool("tasks.testsets.delete", lambda p, prompt: _delete_testset(guard, factory, p, prompt))
    router.add_tool(
        "tasks.testsets.upload_zip",
        lambda p, prompt: _upload_zip(guard, factory, config, p, prompt),
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


def _list_testsets(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    page = params.get("page")
    if page is None:
        page = 1
    try:
        page = max(int(page), 1)
    except (TypeError, ValueError):
        page = 1

    page_size = params.get("page_size")
    if page_size is None:
        page_size = 10
    try:
        page_size = int(page_size)
    except (TypeError, ValueError):
        page_size = 10
    page_size = min(max(page_size, 1), 50)
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.list_testsets(
            hub=hub,
            task_id=task_id,
            page=page,
            page_size=page_size,
        )
        payload = to_payload(result)
        if isinstance(payload, dict):
            payload.setdefault("page", page)
            payload.setdefault("page_size", page_size)
        return payload


def _get_testset(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    testset_id = cast(str, require_param(params, "testset_id"))
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.get_testset(hub=hub, task_id=task_id, testset_id=testset_id)
        return to_payload(result)


def _create_testset(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.testsets.create", hub=hub)
    index = params.get("index")
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.create_testset(hub=hub, task_id=task_id, index=index)
        return to_payload(result)


def _update_testset(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.testsets.update", hub=hub)
    testset_id = cast(str, require_param(params, "testset_id"))
    update_payload_raw = require_param(params, "update")
    if not isinstance(update_payload_raw, Dict):
        raise ValueError("Parameter 'update' must be an object.")
    if not update_payload_raw:
        raise ValueError("Parameter 'update' must include at least one field.")
    update_payload = cast(Dict[str, Any], update_payload_raw)
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.update_testset(hub=hub, task_id=task_id, testset_id=testset_id, **update_payload)
        return to_payload(result)


def _delete_testset(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.testsets.delete", hub=hub)
    testset_id = cast(str, require_param(params, "testset_id"))
    with factory.build_sync_client(prompt) as client:
        result = client.tasks.delete_testset(hub=hub, task_id=task_id, testset_id=testset_id)
        return to_payload(result)


def _upload_zip(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    config: MCPServerConfig,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_id = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.testsets.upload_zip", hub=hub)

    testset_id = cast(str, require_param(params, "testset_id"))
    zip_payload: Any = require_param(params, "zip")
    stream = params.get("stream", True)

    zip_data = coerce_bytes_or_path(zip_payload, allow_paths=config.allow_local_paths)
    enforce_size_limit(zip_data, config.max_upload_mb)

    if not stream:
        with factory.build_sync_client(prompt) as client:
            result = client.tasks.upload_testset_zip(
                hub=hub,
                task_id=task_id,
                testset_id=testset_id,
                zip_path=zip_data,
                stream=False,
            )
            return to_payload(result)

    def _iterator() -> Iterator[Any]:
        with factory.build_sync_client(prompt) as client:
            for event in client.tasks.upload_testset_zip(
                hub=hub,
                task_id=task_id,
                testset_id=testset_id,
                zip_path=zip_data,
                stream=True,
            ):
                yield {"event": to_payload(event)}

    return _iterator()


__all__ = ["register"]
