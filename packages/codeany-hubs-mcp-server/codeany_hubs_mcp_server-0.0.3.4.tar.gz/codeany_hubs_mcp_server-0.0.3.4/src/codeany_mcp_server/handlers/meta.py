"""Handlers for prompts/resources listing with default empty collections."""

from __future__ import annotations

from typing import Any, Dict

from ..auth_guard import MCPAuthorizationGuard
from ..client_factory import ClientFactory
from ..config import MCPServerConfig
from ..router import Router
from ..types import ConsentPrompt


def register(
    router: Router,
    guard: MCPAuthorizationGuard,
    factory: ClientFactory,
    config: MCPServerConfig,
) -> None:
    router.add_tool("prompts.list", _list_prompts)
    router.add_tool("resources.list", _list_resources)
    # Spec-compliant aliases
    router.add_tool("prompts/list", _list_prompts)
    router.add_tool("resources/list", _list_resources)
    router.add_tool("resources/templates/list", _list_resource_templates)


def _list_prompts(params: Dict[str, Any], prompt: ConsentPrompt) -> Dict[str, Any]:
    return {"prompts": [], "nextCursor": ""}


def _list_resources(params: Dict[str, Any], prompt: ConsentPrompt) -> Dict[str, Any]:
    return {"resources": [], "nextCursor": ""}


def _list_resource_templates(params: Dict[str, Any], prompt: ConsentPrompt) -> Dict[str, Any]:
    return {"resourceTemplates": [], "nextCursor": ""}


__all__ = ["register"]
