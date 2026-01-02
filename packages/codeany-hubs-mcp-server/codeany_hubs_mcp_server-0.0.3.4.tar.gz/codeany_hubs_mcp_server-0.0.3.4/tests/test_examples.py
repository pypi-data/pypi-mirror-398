from __future__ import annotations

from codeany_mcp_server.handlers import register_all
from codeany_mcp_server.router import Router
from tests.utils import DummyModel, FactoryStub


class ExamplesResource:
    def __init__(self) -> None:
        self.calls = {}

    def get_examples(self, **kwargs):
        self.calls["get"] = kwargs
        return DummyModel({"examples": []})

    def set_examples(self, **kwargs):
        self.calls["set"] = kwargs
        return DummyModel({"status": "ok"})

    def add_example(self, **kwargs):
        self.calls["add"] = kwargs
        return DummyModel({"status": "ok"})


class FakeClient:
    def __init__(self) -> None:
        self.tasks = ExamplesResource()


def _build_router(factory, guard, config):
    router = Router()
    register_all(router, guard, factory, config)
    return router


def test_examples_set_enforces_limit(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    config.max_examples = 1
    router = _build_router(factory, guard, config)
    handler = router._handlers["tasks.examples.set"]
    result = handler(
        {
            "hub": "hub-1",
            "task_id": "task-1",
            "inputs": ["a", "b"],
        },
        lambda _: True,
    )
    assert "error" in result
    assert result["error"]["code"] == "invalid_request"


def test_examples_add_calls_client(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    router = _build_router(factory, guard, config)
    handler = router._handlers["tasks.examples.add"]
    handler(
        {
            "hub": "hub-1",
            "task_id": "task-1",
            "input": "foo",
            "output": "bar",
            "confirm": True,
        },
        lambda _: True,
    )
    assert client.tasks.calls["add"]["input_data"] == "foo"
