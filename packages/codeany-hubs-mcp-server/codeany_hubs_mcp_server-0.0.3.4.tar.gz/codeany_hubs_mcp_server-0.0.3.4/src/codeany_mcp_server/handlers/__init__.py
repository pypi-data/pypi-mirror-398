"""Handler registration entrypoint."""

from __future__ import annotations

from typing import Callable

from ..auth_guard import MCPAuthorizationGuard
from ..client_factory import ClientFactory
from ..config import MCPServerConfig
from ..router import Router

from . import (
    capabilities,
    examples,
    hubs,
    io_checker,
    limits,
    mcq,
    meta,
    statements,
    system,
    tasks_core,
    testsets,
    tests,
)

RegisterFn = Callable[[Router, MCPAuthorizationGuard, ClientFactory, MCPServerConfig], None]

_REGISTRARS: tuple[RegisterFn, ...] = (
    system.register,
    hubs.register,
    tasks_core.register,
    limits.register,
    statements.register,
    meta.register,
    io_checker.register,
    mcq.register,
    testsets.register,
    tests.register,
    examples.register,
    capabilities.register,
)


def register_all(
    router: Router,
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    config: MCPServerConfig,
) -> None:
    """Register every MCP tool handler on the router."""

    for registrar in _REGISTRARS:
        registrar(router, guard, factory, config)


__all__ = ["register_all"]
