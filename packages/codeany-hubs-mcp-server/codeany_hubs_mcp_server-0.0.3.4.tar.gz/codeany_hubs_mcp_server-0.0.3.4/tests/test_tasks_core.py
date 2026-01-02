from __future__ import annotations

from codeany_mcp_server.handlers import register_all
from codeany_mcp_server.router import Router
from tests.utils import DummyModel, FactoryStub


class RecordingTasks:
    def __init__(self) -> None:
        self.calls = {}

    def delete(self, **kwargs):
        self.calls["delete"] = kwargs
        return DummyModel({"status": "deleted"})

    def create(self, **kwargs):
        self.calls["create"] = kwargs
        return DummyModel({"status": "created"})

    def list(self, hub: str, *, page: int = 1, page_size: int = 20, filters=None):
        self.calls["list"] = {
            "hub": hub,
            "page": page,
            "page_size": page_size,
            "filters": filters,
        }
        return DummyModel({"items": ["task-1", "task-2"], "page": page})

    def get_type(self, **kwargs):
        return DummyModel({"type": "batch"})

    def update_type(self, **kwargs):
        self.calls["update_type"] = kwargs
        return DummyModel({"type": kwargs.get("payload", {}).get("type", "batch")})


class FakeClient:
    def __init__(self) -> None:
        self.tasks = RecordingTasks()


def _build_router(factory, guard, config):
    router = Router()
    register_all(router, guard, factory, config)
    return router


def test_tasks_delete_requires_prompt(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)

    prompts = []

    def prompt(message):
        prompts.append(message)
        return True

    router = _build_router(factory, guard, config)
    handler = router._handlers["tasks.delete"]
    handler({"hub": "hub-1", "task_id": "task-42"}, prompt)

    assert client.tasks.calls["delete"]["hub"] == "hub-1"
    assert any("tasks.delete" in msg for msg in prompts)


def test_tasks_list_returns_payload(guard, config, prompt_accept):
    client = FakeClient()
    factory = FactoryStub(client)
    router = _build_router(factory, guard, config)

    handler = router._handlers["tasks.list"]
    result = handler({"hub": "hub-2", "page": 2, "page_size": 5, "query": "dp"}, prompt_accept)

    assert result == {"items": ["task-1", "task-2"], "page": 2}
    assert client.tasks.calls["list"]["hub"] == "hub-2"
    assert client.tasks.calls["list"]["page_size"] == 5
    assert client.tasks.calls["list"]["filters"] == {"query": "dp"}


def test_tasks_type_get(guard, config, prompt_accept):
    client = FakeClient()
    factory = FactoryStub(client)
    router = _build_router(factory, guard, config)

    handler = router._handlers["tasks.type.get"]
    result = handler({"hub": "hub-1", "task_id": 10}, prompt_accept)

    assert result["type"] == "batch"


def test_tasks_type_update_requires_prompt(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    router = _build_router(factory, guard, config)

    prompts = []

    def prompt(message):
        prompts.append(message)
        return True

    handler = router._handlers["tasks.type.update"]
    handler(
        {
            "hub": "hub-1",
            "task_id": 11,
            "payload": {"type": "mcq"},
        },
        prompt,
    )

    assert client.tasks.calls["update_type"]["payload"]["type"] == "mcq"
    assert any("tasks.type.update" in msg for msg in prompts)
