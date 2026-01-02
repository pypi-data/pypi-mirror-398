from __future__ import annotations

from codeany_mcp_server.handlers import register_all
from codeany_mcp_server.router import Router
from tests.utils import DummyModel, FactoryStub


class DummyTask:
    def __init__(self, task_id: int, slug: str) -> None:
        self.id = task_id
        self.slug = slug


class DummyPage:
    def __init__(self, tasks) -> None:
        self.results = tasks


class StatementTasks:
    def __init__(self) -> None:
        self.calls = {}
        self._task_map = {"task-99": 99, "test-mc-task-3": 303}

    def list(self, hub, *, page=1, page_size=1, filters=None):
        slug = (filters or {}).get("slug")
        if slug in self._task_map:
            return DummyPage([DummyTask(self._task_map[slug], slug)])
        return DummyPage([])

    def get_statements(self, **kwargs):
        self.calls["get"] = kwargs
        lang = kwargs.get("lang")
        return DummyModel({"language": lang})

    def list_statements(self, **kwargs):
        return [DummyModel({"language": "en"})]

    def create_statement_language(self, **kwargs):
        self.calls["create"] = kwargs
        return DummyModel({"language": kwargs["language"]})

    def upsert_statement_language(self, **kwargs):
        self.calls["upsert"] = kwargs
        return DummyModel({"language": kwargs["language"]})

    def delete_statement_language(self, **kwargs):
        self.calls["delete"] = kwargs
        return DummyModel({"ok": True})

    def upload_statement_image(self, **kwargs):
        self.calls["upload_image"] = kwargs
        return DummyModel({"url": "https://example/image.png"})

    def update_statement(self, **kwargs):
        self.calls["update"] = kwargs
        return DummyModel({"ok": True})


class FakeClient:
    def __init__(self) -> None:
        self.tasks = StatementTasks()


def _build_router(factory, guard, config):
    router = Router()
    register_all(router, guard, factory, config)
    return router


def test_upload_image_builds_files_mapping(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    router = _build_router(factory, guard, config)
    handler = router._handlers["tasks.statements.upload_image"]
    payload = {
        "hub": "hub-1",
        "task_id": "task-99",
        "language": "en",
        "image": b"binary",
        "filename": "stmt.png",
        "confirm": True,
    }
    result = handler(payload, lambda _: True)
    files = client.tasks.calls["upload_image"]["files"]
    assert files["file"][0] == "stmt.png"
    assert files["file"][1] == b"binary"
    assert result["url"].endswith(".png")


def test_upload_image_respects_limit(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    config.max_upload_mb = 0  # force failure
    router = _build_router(factory, guard, config)
    handler = router._handlers["tasks.statements.upload_image"]
    response = handler(
        {
            "hub": "hub-1",
            "task_id": "task-99",
            "language": "en",
            "image": b"overflow",
        },
        lambda _: True,
    )
    assert "error" in response
    assert response["error"]["code"] == "invalid_request"


def test_get_statement_accepts_task_alias(guard, config, prompt_accept):
    client = FakeClient()
    factory = FactoryStub(client)
    router = _build_router(factory, guard, config)

    handler = router._handlers["tasks.statements.get"]
    result = handler({"hub": "hub-1", "task": "test-mc-task-3", "language": "en"}, prompt_accept)

    assert result["language"] == "en"
    assert client.tasks.calls["get"]["lang"] == "en"
    assert client.tasks.calls["get"]["task_id"] == 303


def test_update_statement_invokes_sdk(guard, config, prompt_accept):
    client = FakeClient()
    factory = FactoryStub(client)
    router = _build_router(factory, guard, config)

    handler = router._handlers["tasks.statements.update"]
    result = handler(
        {
            "hub": "hub-1",
            "task_id": "task-99",
            "statement_id": 7,
            "payload": {"title": "New title"},
            "confirm": True,
        },
        prompt_accept,
    )

    assert result["ok"] is True
    call = client.tasks.calls["update"]
    assert call["hub"] == "hub-1"
    assert call["task_id"] == 99
    assert call["statement_id"] == 7
    assert call["payload"]["title"] == "New title"
