from __future__ import annotations

from codeany_mcp_server.handlers import register_all
from codeany_mcp_server.router import Router

from tests.utils import DummyModel, FactoryStub


class FakeHubs:
    def list_mine(self):
        return [DummyModel({"id": "hub-1"})]

    def detail(self, hub: str):
        return DummyModel({"id": hub, "name": "Sample Hub"})


class FakeClient:
    hubs = FakeHubs()


def _build_router(factory, guard, config):
    router = Router()
    register_all(router, guard, factory, config)
    return router


def test_hubs_list_mine(guard, config, prompt_accept):
    factory = FactoryStub(FakeClient())
    router = _build_router(factory, guard, config)
    handler = router._handlers["hubs.list_mine"]
    result = handler({}, prompt_accept)
    assert result == [{"id": "hub-1"}]


def test_hubs_detail(guard, config, prompt_accept):
    factory = FactoryStub(FakeClient())
    router = _build_router(factory, guard, config)
    handler = router._handlers["hubs.detail"]
    result = handler({"hub": "hub-1"}, prompt_accept)
    assert result["id"] == "hub-1"
