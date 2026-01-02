"""Handlers for task statements management."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union, cast

from ..auth_guard import MCPAuthorizationGuard
from ..client_factory import ClientFactory
from ..config import MCPServerConfig
from ..router import Router
from ..types import ConsentPrompt
from ..io_utils import coerce_bytes_or_path, enforce_size_limit, files_tuple
from ._utils import require_confirm, require_param, to_payload, to_payload_list


def register(
    router: Router,
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    config: MCPServerConfig,
) -> None:
    router.add_tool(
        "tasks.statements.get",
        lambda params, prompt: _get_statement(guard, factory, params, prompt),
    )
    router.add_tool(
        "tasks.statements.list",
        lambda params, prompt: _list_statements(guard, factory, params, prompt),
    )
    router.add_tool(
        "tasks.statements.create_lang",
        lambda params, prompt: _create_language(guard, factory, params, prompt),
    )
    router.add_tool(
        "tasks.statements.delete_lang",
        lambda params, prompt: _delete_language(guard, factory, params, prompt),
    )
    router.add_tool(
        "tasks.statements.update",
        lambda params, prompt: _update_statement(guard, factory, params, prompt),
    )
    router.add_tool(
        "tasks.statements.upload_image",
        lambda params, prompt: _upload_image(guard, factory, params, prompt, config),
    )


def _ensure_context(
    guard: MCPAuthorizationGuard,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> tuple[str, Union[str, int]]:
    guard.ensure_session_consent(prompt)
    hub = str(require_param(params, "hub"))
    task_ref = params.get("task_id", params.get("task"))
    if task_ref is None:
        raise ValueError("Missing required parameter 'task_id'.")
    guard.ensure_hub_allowed(hub)
    return hub, task_ref


def _get_statement(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_ref = _ensure_context(guard, params, prompt)
    language = params.get("language", params.get("lang"))
    if language is not None:
        language = str(language)
    with factory.build_sync_client(prompt) as client:
        task_id = _resolve_task_id(client, hub, task_ref)
        result = client.tasks.get_statements(hub=hub, task_id=task_id, language=language)
        return to_payload(result)


def _list_statements(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_ref = _ensure_context(guard, params, prompt)
    with factory.build_sync_client(prompt) as client:
        task_id = _resolve_task_id(client, hub, task_ref)
        return to_payload_list(client.tasks.list_statements(hub=hub, task_id=task_id))


def _create_language(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_ref = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.statements.create_lang", hub=hub)
    language = cast(str, require_param(params, "language"))
    content = cast(Dict[str, Any], require_param(params, "content"))
    with factory.build_sync_client(prompt) as client:
        task_id = _resolve_task_id(client, hub, task_ref)
        result = client.tasks.create_statement_language(
            hub=hub,
            task_id=task_id,
            language=language,
            content=content,
        )
        return to_payload(result)


def _delete_language(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_ref = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.statements.delete_lang", hub=hub)
    language = cast(str, require_param(params, "language"))
    with factory.build_sync_client(prompt) as client:
        task_id = _resolve_task_id(client, hub, task_ref)
        result = client.tasks.delete_statement_language(hub=hub, task_id=task_id, language=language)
        return to_payload(result)


def _upload_image(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
    config: MCPServerConfig,
) -> Any:
    hub, task_ref = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.statements.upload_image", hub=hub)

    language = cast(str, require_param(params, "language"))
    image_payload: Any = require_param(params, "image")
    filename: Optional[str] = params.get("filename")
    content_type: Optional[str] = params.get("content_type")

    data = coerce_bytes_or_path(image_payload, allow_paths=config.allow_local_paths)
    enforce_size_limit(data, config.max_upload_mb)
    file_mapping = files_tuple("file", data, filename=filename, content_type=content_type)

    with factory.build_sync_client(prompt) as client:
        task_id = _resolve_task_id(client, hub, task_ref)
        result = client.tasks.upload_statement_image(
            hub=hub,
            task_id=task_id,
            language=language,
            files=file_mapping,
        )
        return to_payload(result)


def _update_statement(
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    params: Dict[str, Any],
    prompt: ConsentPrompt,
) -> Any:
    hub, task_ref = _ensure_context(guard, params, prompt)
    if not require_confirm(params):
        guard.ensure_destructive_consent(prompt, op_name="tasks.statements.update", hub=hub)
    statement_id = cast(int, require_param(params, "statement_id"))
    payload = cast(Dict[str, Any], require_param(params, "payload"))
    with factory.build_sync_client(prompt) as client:
        task_id = _resolve_task_id(client, hub, task_ref)
        result = client.tasks.update_statement(
            hub=hub,
            task_id=task_id,
            statement_id=statement_id,
            payload=payload,
        )
        return to_payload(result)


def _resolve_task_id(client: Any, hub: str, task_ref: Union[str, int]) -> int:
    """Allow handlers to accept either numeric task IDs or task slugs."""

    if isinstance(task_ref, int):
        return task_ref

    task_str = str(task_ref).strip()
    if task_str.isdigit():
        return int(task_str)

    page = client.tasks.list(hub=hub, page=1, page_size=1, filters={"slug": task_str})
    for task in getattr(page, "results", []):
        task_id = getattr(task, "id", None)
        if task_id is not None:
            return int(task_id)

    raise ValueError(f"Task '{task_str}' not found in hub '{hub}'.")


__all__ = ["register"]
