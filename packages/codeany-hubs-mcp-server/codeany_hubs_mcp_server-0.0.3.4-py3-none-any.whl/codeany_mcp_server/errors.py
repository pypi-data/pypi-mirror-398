"""Error normalization utilities for the MCP server."""

from __future__ import annotations

from collections.abc import Generator, Iterator
from typing import Any, Callable, Dict, TYPE_CHECKING

from .auth_guard import HubNotAllowedError

if TYPE_CHECKING:  # pragma: no cover
    from codeany_hub.core.errors import (
        ApiError as _ApiError,
        AuthError as _AuthError,
        ConsentRejectedError as _ConsentRejectedError,
        NotFoundError as _NotFoundError,
        RateLimitError as _RateLimitError,
        ValidationError as _ValidationError,
    )
else:  # pragma: no cover
    try:
        from codeany_hub.core.errors import (
            ApiError as _ApiError,
            AuthError as _AuthError,
            ConsentRejectedError as _ConsentRejectedError,
            NotFoundError as _NotFoundError,
            RateLimitError as _RateLimitError,
            ValidationError as _ValidationError,
        )
    except ImportError:

        class _ApiError(Exception):
            status_code: int = 500

        class _AuthError(_ApiError):
            ...

        class _ConsentRejectedError(Exception):
            ...

        class _NotFoundError(_ApiError):
            status_code = 404

        class _RateLimitError(_ApiError):
            status_code = 429

        class _ValidationError(_ApiError):
            status_code = 400


ApiError = _ApiError
AuthError = _AuthError
ConsentRejectedError = _ConsentRejectedError
NotFoundError = _NotFoundError
RateLimitError = _RateLimitError
ValidationError = _ValidationError


ErrorPayload = Dict[str, Any]
Handler = Callable[..., Any]


def _extract_details(exc: Exception) -> Dict[str, Any]:
    detail = getattr(exc, "detail", None) or getattr(exc, "details", None)
    payload: Dict[str, Any] = {}
    if detail:
        payload["detail"] = detail
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        payload["status_code"] = status_code
    return payload


def to_mcp_error(exc: Exception) -> ErrorPayload:
    """Map SDK or server exceptions to a JSON-serializable MCP error payload."""

    base: ErrorPayload = {"message": str(exc)}

    if isinstance(exc, HubNotAllowedError):
        base["code"] = "hub_not_allowed"
        return base
    if isinstance(exc, ConsentRejectedError):
        base["code"] = "consent_rejected"
        return base
    if isinstance(exc, NotFoundError):
        base["code"] = "not_found"
        base["data"] = _extract_details(exc)
        return base
    if isinstance(exc, AuthError):
        base["code"] = "auth_error"
        base["data"] = _extract_details(exc)
        return base
    if isinstance(exc, RateLimitError):
        base["code"] = "rate_limited"
        base["data"] = _extract_details(exc)
        return base
    if isinstance(exc, ValidationError):
        base["code"] = "validation_error"
        base["data"] = _extract_details(exc)
        return base
    if isinstance(exc, ApiError):
        base["code"] = "api_error"
        base["data"] = _extract_details(exc)
        return base
    if isinstance(exc, ValueError):
        base["code"] = "invalid_request"
        return base

    base["code"] = "internal_error"
    return base


def wrap_handler(handler: Handler) -> Handler:
    """
    Wrap a handler so that unexpected exceptions are converted into MCP error dicts.

    The returned callable preserves generator semantics: if the handler yields,
    the resulting wrapper will yield dictionaries. Any exception raised before
    or during iteration is transformed into a single error payload.
    """

    def _iterator(it: Iterator[Any]) -> Iterator[Any]:
        try:
            for item in it:
                yield item
        except Exception as error:  # pragma: no cover - conversion handled by router tests
            yield {"error": to_mcp_error(error)}

    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            result = handler(*args, **kwargs)
        except Exception as error:
            return {"error": to_mcp_error(error)}

        if isinstance(result, dict) and "error" in result:
            return result
        if isinstance(result, Generator):
            return _iterator(iter(result))
        if isinstance(result, Iterator):
            return _iterator(result)
        return result

    return _wrapper


__all__ = ["to_mcp_error", "wrap_handler"]
