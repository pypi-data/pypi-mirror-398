"""Shared type definitions for the CodeAny MCP server."""

from __future__ import annotations

from typing import Callable, Protocol

ConsentPrompt = Callable[[str], bool]


class PromptCallable(Protocol):
    """Protocol representing the consent prompt callable signature."""

    def __call__(self, message: str) -> bool:
        ...


__all__ = ["ConsentPrompt", "PromptCallable"]
