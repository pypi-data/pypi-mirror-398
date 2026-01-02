from __future__ import annotations

from codeany_mcp_server.handlers import register_all
from codeany_mcp_server.router import Router

from tests.utils import FactoryStub


def test_prompts_and_resources_list(guard, config, prompt_accept):
    factory = FactoryStub(client=None)
    router = Router()
    register_all(router, guard, factory, config)

    prompts = router._handlers["prompts.list"]({}, prompt_accept)
    resources = router._handlers["resources.list"]({}, prompt_accept)

    assert prompts == {"prompts": [], "nextCursor": ""}
    assert resources == {"resources": [], "nextCursor": ""}
