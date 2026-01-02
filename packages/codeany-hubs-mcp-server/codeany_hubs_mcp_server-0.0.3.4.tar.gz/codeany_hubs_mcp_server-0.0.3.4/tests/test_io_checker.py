from __future__ import annotations

from codeany_mcp_server.handlers import register_all
from codeany_mcp_server.router import Router
from tests.utils import DummyModel, FactoryStub


class IOResource:
    def __init__(self) -> None:
        self.calls = {}

    def get_io(self, **kwargs):
        self.calls["get"] = kwargs
        return DummyModel({"checker": "default"})

    def update_io(self, **kwargs):
        self.calls["update"] = kwargs
        return DummyModel({"checker": kwargs["io"]["checker"]})


class FakeClient:
    def __init__(self) -> None:
        self.tasks = IOResource()


def _build_router(factory, guard, config):
    router = Router()
    register_all(router, guard, factory, config)
    return router


def test_update_io_forwards_payload(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    router = _build_router(factory, guard, config)
    handler = router._handlers["tasks.io.update"]
    payload = {
        "hub": "hub-1",
        "task_id": "task-1",
        "io": {"checker": "custom"},
        "confirm": True,
    }
    result = handler(payload, lambda _: True)
    assert client.tasks.calls["update"]["io"] == {"checker": "custom"}
    assert result["checker"] == "custom"
