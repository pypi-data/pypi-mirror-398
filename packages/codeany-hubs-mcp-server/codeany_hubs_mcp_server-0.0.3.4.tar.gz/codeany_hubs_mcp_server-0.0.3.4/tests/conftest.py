from __future__ import annotations

from typing import Any

import pytest

from codeany_mcp_server.auth_guard import MCPAuthorizationGuard
from codeany_mcp_server.config import MCPServerConfig
from tests.utils import DummyModel


@pytest.fixture
def config() -> MCPServerConfig:
    return MCPServerConfig()


@pytest.fixture
def guard(config: MCPServerConfig) -> MCPAuthorizationGuard:
    return MCPAuthorizationGuard(config)


@pytest.fixture
def prompt_accept() -> Any:
    return lambda message: True


@pytest.fixture
def prompt_reject() -> Any:
    return lambda message: False


@pytest.fixture
def dummy_model() -> DummyModel:
    return DummyModel
