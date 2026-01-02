"""Authorization guard enforcing consent and hub allowlist policies."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from .config import MCPServerConfig
from .types import ConsentPrompt

if TYPE_CHECKING:  # pragma: no cover
    from codeany_hub.core.errors import ConsentRejectedError as _ConsentRejectedError
else:  # pragma: no cover
    try:
        from codeany_hub.core.errors import ConsentRejectedError as _ConsentRejectedError
    except ImportError:

        class _ConsentRejectedError(RuntimeError):
            """Raised when a user rejects an MCP consent prompt."""


ConsentRejectedError = _ConsentRejectedError


class HubNotAllowedError(RuntimeError):
    """Raised when a requested hub is not in the allowlist."""


_SESSION_CONSENT_PROMPT = (
    "CodeAny Hub MCP server wants to connect to your CodeAny account. Allow this session?"
)
_DESTRUCTIVE_PROMPT_TEMPLATE = (
    "Authorize operation '{op_name}' on hub '{hub}'? This may modify existing tasks."
)


@dataclass(slots=True)
class MCPAuthorizationState:
    """Thread-safe state tracker for session consent."""

    granted: Optional[bool] = None
    lock: threading.Lock = field(default_factory=threading.Lock)


class MCPAuthorizationGuard:
    """Centralized consent and allowlist enforcement."""

    def __init__(self, config: MCPServerConfig) -> None:
        self._config = config
        self._state = MCPAuthorizationState()

    def ensure_session_consent(self, prompt: ConsentPrompt) -> None:
        """
        Ensure the operator accepted the session-level consent prompt.

        The prompt is shown once per process unless the operator rejects it,
        in which case the rejection is cached and propagated to subsequent calls.
        """

        if not self._config.ask_on_start:
            # Consent prompts are disabled – treat as already accepted.
            self._state.granted = True
            return

        with self._state.lock:
            if self._state.granted is True:
                return
            if self._state.granted is False:
                raise ConsentRejectedError("Session consent previously rejected.")

            message = self._config.consent_message or _SESSION_CONSENT_PROMPT
            accepted = prompt(message)
            self._state.granted = accepted
            if not accepted:
                raise ConsentRejectedError("Session consent rejected by operator.")

    def ensure_destructive_consent(
        self,
        prompt: ConsentPrompt,
        *,
        op_name: str,
        hub: str,
    ) -> None:
        """Request explicit consent for destructive operations when required."""

        if not self._config.ask_on_destructive_ops:
            return

        if self._config.destructive_message_provider:
            message = self._config.destructive_message_provider(op_name, hub)
        else:
            message = _DESTRUCTIVE_PROMPT_TEMPLATE.format(op_name=op_name, hub=hub)

        accepted = prompt(message)
        if not accepted:
            raise ConsentRejectedError(f"Destructive operation '{op_name}' rejected for hub '{hub}'.")

    def ensure_hub_allowed(self, hub: str) -> None:
        """Validate the requested hub against the configured allowlist."""

        if self._config.hub_allowlist is None:
            return
        if hub not in self._config.hub_allowlist:
            raise HubNotAllowedError(f"Hub '{hub}' is not in the MCP hub allowlist.")


__all__ = ["MCPAuthorizationGuard", "HubNotAllowedError", "ConsentRejectedError"]
