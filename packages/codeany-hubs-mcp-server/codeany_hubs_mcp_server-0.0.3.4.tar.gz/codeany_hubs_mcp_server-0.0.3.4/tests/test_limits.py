from __future__ import annotations

from codeany_mcp_server.handlers import register_all
from codeany_mcp_server.router import Router
from tests.utils import DummyModel, FactoryStub


class LimitsTasks:
    def __init__(self) -> None:
        self.calls = {}

    def get_limits(self, **kwargs):
        self.calls["get_limits"] = kwargs
        return DummyModel({"limit": 10})

    def update_limits(self, **kwargs):
        self.calls["update_limits"] = kwargs
        return DummyModel({"time_limit": kwargs["time_limit"], "memory_limit": kwargs["memory_limit"]})


class FakeClient:
    def __init__(self) -> None:
        self.tasks = LimitsTasks()


def _build_router(factory, guard, config):
    router = Router()
    register_all(router, guard, factory, config)
    return router


def test_limits_update_passes_payload(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    router = _build_router(factory, guard, config)
    handler = router._handlers["tasks.limits.update"]
    payload = {
        "hub": "hub-1",
        "task_id": "task-1",
        "time_limit": 1500,
        "memory_limit": 256,
    }
    handler(payload, lambda _: True)
    call = client.tasks.calls["update_limits"]
    assert call["time_limit"] == 1500
    assert call["memory_limit"] == 256


def test_limits_update_accepts_limits_block(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    router = _build_router(factory, guard, config)
    handler = router._handlers["tasks.limits.update"]
    payload = {
        "hub": "hub-1",
        "task_id": "task-1",
        "limits": {"time_limit": 2000, "memory_limit": 512},
    }
    handler(payload, lambda _: True)
    call = client.tasks.calls["update_limits"]
    assert call["time_limit"] == 2000
    assert call["memory_limit"] == 512
