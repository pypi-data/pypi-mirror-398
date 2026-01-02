from __future__ import annotations

from codeany_mcp_server.handlers import register_all
from codeany_mcp_server.router import Router
from tests.utils import DummyModel, FactoryStub


class TestsResource:
    def __init__(self) -> None:
        self.calls = {}

    def get_testcase(self, **kwargs):
        self.calls["get"] = kwargs
        return DummyModel({"index": kwargs["index"]})

    def upload_single_test(self, **kwargs):
        self.calls["upload"] = kwargs
        return None

    def delete_testcase(self, **kwargs):
        self.calls["delete_one"] = kwargs
        return DummyModel({"deleted": kwargs["index"]})

    def delete_testcases(self, **kwargs):
        self.calls["delete_many"] = kwargs
        return DummyModel({"deleted": kwargs["indexes"]})


class FakeClient:
    def __init__(self) -> None:
        self.tasks = TestsResource()


def _build_router(factory, guard, config):
    router = Router()
    register_all(router, guard, factory, config)
    return router


def test_upload_single_compiles_files(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    router = _build_router(factory, guard, config)
    handler = router._handlers["tasks.tests.upload_single"]
    result = handler(
        {
            "hub": "hub-1",
            "task_id": "task-1",
            "testset_id": "set-1",
            "input_data": b"in",
            "answer_data": b"out",
            "confirm": True,
        },
        lambda _: True,
    )
    call = client.tasks.calls["upload"]
    assert call["input_path"] == b"in"
    assert call["answer_path"] == b"out"
    assert result["status"] == "uploaded"
