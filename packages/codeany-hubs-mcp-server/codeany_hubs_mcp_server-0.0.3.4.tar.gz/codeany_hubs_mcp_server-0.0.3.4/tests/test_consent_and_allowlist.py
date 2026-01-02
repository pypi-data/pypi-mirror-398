from __future__ import annotations

import pytest

from codeany_mcp_server.auth_guard import ConsentRejectedError, HubNotAllowedError


def test_session_consent_accepts_once(guard, prompt_accept):
    guard.ensure_session_consent(prompt_accept)
    # second call should be no-op
    guard.ensure_session_consent(prompt_accept)


def test_session_consent_rejects(guard, prompt_reject):
    with pytest.raises(ConsentRejectedError):
        guard.ensure_session_consent(prompt_reject)
    with pytest.raises(ConsentRejectedError):
        guard.ensure_session_consent(prompt_reject)


def test_hub_allowlist_blocks(guard, config, prompt_accept):
    config.hub_allowlist = {"sandbox"}
    guard.ensure_session_consent(prompt_accept)
    with pytest.raises(HubNotAllowedError):
        guard.ensure_hub_allowed("prod")
