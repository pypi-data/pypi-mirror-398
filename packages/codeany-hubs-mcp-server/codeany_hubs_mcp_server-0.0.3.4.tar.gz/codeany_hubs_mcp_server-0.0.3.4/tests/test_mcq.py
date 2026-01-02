from __future__ import annotations

from codeany_mcp_server.handlers import register_all
from codeany_mcp_server.router import Router
from tests.utils import DummyModel, FactoryStub


class MCQResource:
    def __init__(self) -> None:
        self.calls = {}

    def get_config(self, **kwargs):
        self.calls["get_config"] = kwargs
        return DummyModel({"question": "What is the capital?"})

    def replace_config(self, **kwargs):
        self.calls["replace_config"] = kwargs
        return DummyModel({"status": "replaced"})

    def patch_config(self, **kwargs):
        self.calls["patch_config"] = kwargs
        return DummyModel({"status": "patched"})

    def set_correct(self, **kwargs):
        self.calls["set_correct"] = kwargs
        return DummyModel({"status": "updated"})


class HubsResource:
    def __init__(self) -> None:
        self.mcq = MCQResource()


class FakeClient:
    def __init__(self) -> None:
        self.hubs = HubsResource()


def _build_router(factory, guard, config):
    router = Router()
    register_all(router, guard, factory, config)
    return router


def test_mcq_get_config_returns_payload(guard, config, prompt_accept):
    client = FakeClient()
    factory = FactoryStub(client)
    router = _build_router(factory, guard, config)

    handler = router._handlers["tasks.mcq.get_config"]
    result = handler({"hub": "hub-main", "task_id": 7}, prompt_accept)

    assert result["question"] == "What is the capital?"
    assert client.hubs.mcq.calls["get_config"] == {"hub": "hub-main", "task_id": 7}


def test_mcq_replace_config_requires_destructive_prompt(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    router = _build_router(factory, guard, config)

    prompts = []

    def prompt(message):
        prompts.append(message)
        return True

    handler = router._handlers["tasks.mcq.replace_config"]
    handler(
        {
            "hub": "hub-main",
            "task_id": 99,
            "config": {"question": "Updated?", "options": []},
        },
        prompt,
    )

    assert client.hubs.mcq.calls["replace_config"]["hub"] == "hub-main"
    assert any("tasks.mcq.replace_config" in msg for msg in prompts)


def test_mcq_patch_config_uses_payload_and_confirm(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    router = _build_router(factory, guard, config)

    prompts = []

    def prompt(message):
        prompts.append(message)
        return True

    handler = router._handlers["tasks.mcq.patch_config"]
    handler(
        {
            "hub": "hub-main",
            "task_id": 77,
            "patch": {"allow_multiple": True},
            "confirm": True,
        },
        prompt,
    )

    assert client.hubs.mcq.calls["patch_config"]["patch"] == {"allow_multiple": True}
    assert prompts == []


def test_mcq_set_correct_prompts_without_confirm(guard, config):
    client = FakeClient()
    factory = FactoryStub(client)
    guard.ensure_session_consent(lambda _: True)
    router = _build_router(factory, guard, config)

    prompts = []

    def prompt(message):
        prompts.append(message)
        return True

    handler = router._handlers["tasks.mcq.set_correct"]
    handler(
        {
            "hub": "hub-main",
            "task_id": 5,
            "correct_option_ids": ["B"],
        },
        prompt,
    )

    assert client.hubs.mcq.calls["set_correct"]["correct_option_ids"] == ["B"]
    assert any("tasks.mcq.set_correct" in msg for msg in prompts)
