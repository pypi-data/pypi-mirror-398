from __future__ import annotations

from codeany_mcp_server.handlers import register_all
from codeany_mcp_server.router import Router

from tests.utils import FactoryStub


def test_initialize_returns_capabilities_and_tools(guard, config, prompt_accept):
    factory = FactoryStub(client=None)
    router = Router()
    register_all(router, guard, factory, config)

    handler = router._handlers["initialize"]
    result = handler({}, prompt_accept)

    assert "capabilities" in result and "serverCapabilities" in result
    assert "serverInfo" in result
    assert "tools" in result and isinstance(result["tools"], list)
    assert "toolNames" in result and set(result["toolNames"])
    assert any(tool["name"] == "tasks.create" for tool in result["tools"])
