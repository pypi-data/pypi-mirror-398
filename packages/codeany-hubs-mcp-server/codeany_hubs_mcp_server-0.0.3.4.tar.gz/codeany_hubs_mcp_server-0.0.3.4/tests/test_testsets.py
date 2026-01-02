from __future__ import annotations

from codeany_mcp_server.handlers import register_all
from codeany_mcp_server.router import Router
from tests.utils import DummyModel, FactoryStub


class TestsetTasks:
    def __init__(self) -> None:
        self.calls = {}

    def list_testsets(self, **kwargs):
        self.calls["list"] = kwargs
        return DummyModel({"items": []})

    def get_testset(self, **kwargs):
        self.calls["get"] = kwargs
        return DummyModel({"id": kwargs["testset_id"]})

    def create_testset(self, **kwargs):
        self.calls["create"] = kwargs
        return DummyModel({"id": "new"})

    def update_testset(self, **kwargs):
        self.calls["update"] = kwargs
        return DummyModel({"id": kwargs["testset_id"], "index": kwargs.get("index")})

    def delete_testset(self, **kwargs):
        self.calls["delete"] = kwargs
        return DummyModel({"status": "deleted"})

    def upload_testset_zip(self, **kwargs):
        self.calls["upload_zip"] = kwargs
        if kwargs.get("stream"):
            def _events():
                yield DummyModel({"status": "processing"})
                yield DummyModel({"status": "done"})
            return _events()
        return DummyModel({"status": "done"})


class FakeClient:
    def __init__(self) -> None:
        self.tasks = TestsetTasks()


def _build_router(factory, guard, config):
    router = Router()
    register_all(router, guard, factory, config)
    return router


def test_upload_zip_streams_events(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    router = _build_router(factory, guard, config)
    handler = router._handlers["tasks.testsets.upload_zip"]
    iterator = handler(
        {
            "hub": "hub-1",
            "task_id": "task-1",
            "testset_id": 5,
            "zip": b"zipdata",
            "confirm": True,
        },
        lambda _: True,
    )
    events = list(iterator)
    assert events[0]["event"]["status"] == "processing"
    assert client.tasks.calls["upload_zip"]["stream"] is True
    assert client.tasks.calls["upload_zip"]["zip_path"] == b"zipdata"


def test_list_testsets_defaults_page_and_size(guard, config, prompt_accept):
    client = FakeClient()
    factory = FactoryStub(client)
    router = _build_router(factory, guard, config)

    handler = router._handlers["tasks.testsets.list"]
    result = handler({"hub": "hub-1", "task_id": "task-1"}, prompt_accept)

    call = client.tasks.calls["list"]
    assert call["page"] == 1
    assert call["page_size"] == 10
    assert result["page"] == 1
    assert result["page_size"] == 10


def test_list_testsets_clamps_page_size(guard, config, prompt_accept):
    client = FakeClient()
    factory = FactoryStub(client)
    router = _build_router(factory, guard, config)

    handler = router._handlers["tasks.testsets.list"]
    result = handler({"hub": "hub-1", "task_id": "task-1", "page": -5, "page_size": 500}, prompt_accept)

    call = client.tasks.calls["list"]
    assert call["page"] == 1
    assert call["page_size"] == 50
    assert result["page_size"] == 50


def test_update_testset_forwards_fields(guard, config, prompt_accept):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    router = _build_router(factory, guard, config)

    handler = router._handlers["tasks.testsets.update"]
    result = handler(
        {
            "hub": "hub-1",
            "task_id": "task-1",
            "testset_id": 9,
            "update": {"index": 2, "score": 50},
            "confirm": True,
        },
        prompt_accept,
    )

    call = client.tasks.calls["update"]
    assert call["testset_id"] == 9
    assert call["index"] == 2
    assert call["score"] == 50
    assert result["index"] == 2
