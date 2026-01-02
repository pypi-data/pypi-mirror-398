from __future__ import annotations

from __future__ import annotations

from codeany_mcp_server.handlers import register_all
from codeany_mcp_server.handlers.capabilities import get_tool_details
from codeany_mcp_server.router import Router

from tests.utils import FactoryStub


class DummyHubs:
    def list_mine(self):
        return [{"slug": "stub-hub"}]


class DummyClient:
    def __init__(self) -> None:
        self.hubs = DummyHubs()


def test_tools_capabilities_and_list(guard, config, prompt_accept):
    factory = FactoryStub(client=None)
    router = Router()
    register_all(router, guard, factory, config)

    caps_handler = router.lookup_handler("tools.capabilities")
    list_handler = router.lookup_handler("tools.list")
    list_slash_handler = router.lookup_handler("tools/list")

    assert caps_handler and list_handler and list_slash_handler

    caps = caps_handler({}, prompt_accept)
    listed = list_handler({}, prompt_accept)
    listed_slash = list_slash_handler({}, prompt_accept)

    tool_names = [tool["name"] for tool in listed["tools"]]
    assert set(caps["tools"]) == set(tool_names)
    assert all(name.replace(".", "_") == name for name in tool_names)
    assert caps["nextCursor"] == ""
    assert listed["nextCursor"] == ""
    assert listed_slash == listed
    assert all("description" in tool for tool in listed["tools"])
    assert all(tool["inputSchema"]["type"] == "object" for tool in listed["tools"])
    assert all("metadata" in tool and "original" in tool["metadata"] for tool in listed["tools"])


def test_tools_call_delegates_to_handler(guard, config, prompt_accept):
    factory = FactoryStub(client=DummyClient())
    router = Router()
    register_all(router, guard, factory, config)

    call_handler = router.lookup_handler("tools/call")
    assert call_handler

    first_tool = get_tool_details()[0]
    sanitized = first_tool["name"]
    original = first_tool["metadata"]["original"]

    # Ensure sanitized names and original dotted names both work
    result = call_handler({"name": sanitized, "arguments": {}}, prompt_accept)
    assert result["isError"] is False
    assert result["content"]

    result_namespaced = call_handler({"name": f"codeany_hubs/{sanitized}", "arguments": {}}, prompt_accept)
    assert result_namespaced["isError"] is False
    assert result_namespaced["content"]

    result_original = call_handler({"name": original, "arguments": {}}, prompt_accept)
    assert result_original["isError"] is False
    assert result_original["content"]
