"""Minimal JSON-RPC router for the CodeAny Hub MCP server."""

from __future__ import annotations

import json
import os
import sys
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, BinaryIO, Callable, Dict, List, Optional

from .errors import to_mcp_error, wrap_handler
from .logging_config import get_logger
from .types import ConsentPrompt

HandlerCallable = Callable[[Dict[str, Any], ConsentPrompt], Any]


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    lowered = val.strip().lower()
    return lowered in {"1", "true", "yes", "y", "on"}


def _default_prompt(message: str) -> bool:
    """Consent prompt that is safe for stdio JSON-RPC transports.

    If stdin is a TTY, prompt interactively.
    Otherwise, DO NOT read from stdin (which would corrupt the transport). Fall back to
    environment-controlled defaults:
      - MCP_NONINTERACTIVE_CONSENT (default: true) for session prompts
      - MCP_NONINTERACTIVE_CONSENT_DESTRUCTIVE (default: false) for destructive prompts
    """

    # Determine if we can safely read from stdin
    try:
        is_tty = sys.stdin.isatty()
    except Exception:
        is_tty = False

    if not is_tty:
        # Heuristic: our default destructive prompt text includes "Authorize operation".
        is_destructive = "authorize operation" in message.lower()
        choice = (
            _env_bool("MCP_NONINTERACTIVE_CONSENT_DESTRUCTIVE", False)
            if is_destructive
            else _env_bool("MCP_NONINTERACTIVE_CONSENT", True)
        )
        sys.stderr.write(f"{message} [auto={'y' if choice else 'n'}]\n")
        sys.stderr.flush()
        return choice

    sys.stderr.write(f"{message} [y/N]: ")
    sys.stderr.flush()
    answer = sys.stdin.readline().strip().lower()
    return answer in {"y", "yes"}


@dataclass(slots=True)
class RegisteredHandler:
    name: str
    callable: HandlerCallable


class Router:
    """Simple stdio router that invokes registered handlers."""

    def __init__(
        self,
        *,
        prompt: Optional[ConsentPrompt] = None,
        max_concurrency: int = 8,
    ) -> None:
        self._prompt = prompt or _default_prompt
        self._handlers: Dict[str, HandlerCallable] = {}
        self._semaphore = threading.Semaphore(max_concurrency) if max_concurrency > 0 else None
        self._logger = get_logger("router")
        self._response_mode: str = "content-length"

    def add_tool(self, name: str, handler: HandlerCallable) -> None:
        """Register a tool handler."""

        if name in self._handlers:
            raise ValueError(f"Handler '{name}' already registered.")
        self._handlers[name] = wrap_handler(handler)
        self._logger.debug("Registered tool handler '%s'", name)

    def lookup_handler(self, name: str) -> Optional[HandlerCallable]:
        """Expose registered handlers for adapters that need direct access."""

        return self._handlers.get(name)

    def list_tools(self) -> List[str]:
        """Return all registered tool names."""

        return list(self._handlers.keys())

    def run_stdio(self) -> int:
        """Process JSON-RPC requests framed via Content-Length headers."""

        stdin = sys.stdin.buffer
        self._logger.info("Router entering stdio loop")

        while True:
            message, mode = self._read_message(stdin)
            if message is None:
                break

            try:
                request = json.loads(message.decode("utf-8"))
            except json.JSONDecodeError as error:
                self._write_error(None, "parse_error", f"Invalid JSON payload: {error}")
                self._logger.warning("Failed to parse JSON request: %s", error)
                continue

            self._logger.debug("Received request: %s", request)
            self._response_mode = mode
            if self._semaphore:
                acquired = self._semaphore.acquire(timeout=0.0)
                if not acquired:
                    self._write_error(request.get("id"), "server_busy", "Router is at capacity.")
                    self._logger.warning("Router capacity reached; rejecting request %s", request.get("id"))
                    continue

            try:
                self._dispatch(request)
            finally:
                if self._semaphore:
                    self._semaphore.release()

        return 0

    def _read_message(self, stdin: BinaryIO) -> tuple[Optional[bytes], str]:
        """Read either a Content-Length framed JSON message or a newline-delimited JSON line."""

        while True:
            chunk = stdin.readline()
            if not chunk:
                return None, self._response_mode

            if chunk in (b"\r\n", b"\n"):
                continue

            stripped = chunk.strip()
            if not stripped:
                continue

            lowered = stripped.lower()
            if lowered.startswith(b"content-length:"):
                try:
                    content_length = int(stripped.split(b":", 1)[1].strip())
                except ValueError:
                    self._logger.warning("Invalid Content-Length header: %s", stripped)
                    continue

                while True:
                    header_line = stdin.readline()
                    if not header_line:
                        return None, self._response_mode
                    if header_line in (b"\r\n", b"\n"):
                        break

                if content_length <= 0:
                    return b"{}", "content-length"
                return stdin.read(content_length), "content-length"

            return stripped, "newline"

    def _dispatch(self, request: Dict[str, Any]) -> None:
        # Determine if this is a notification (no id field per JSON-RPC 2.0)
        has_id = "id" in request
        request_id = request.get("id") if has_id else None
        method = request.get("method")
        params = request.get("params") or {}

        if not isinstance(method, str):
            if has_id:
                self._write_error(request_id, "invalid_request", "Missing or invalid method name.")
            self._logger.warning("Request %s missing method name", request_id)
            return

        handler = self._handlers.get(method)

        # Notifications MUST NOT receive any response.
        if not has_id:
            if handler is None:
                self._logger.debug("Ignoring unknown notification '%s'", method)
                return
            try:
                handler(params, self._prompt)
            except Exception:
                self._logger.exception("Notification handler '%s' raised an exception", method)
            return

        if handler is None:
            self._write_error(request_id, "method_not_found", f"No handler registered for '{method}'.")
            self._logger.warning("Request %s called unregistered method '%s'", request_id, method)
            return

        self._logger.info("Dispatching method '%s' with id=%s params=%s", method, request_id, params)
        try:
            result = handler(params, self._prompt)
            self._logger.debug("Handler '%s' produced result type=%s", method, type(result).__name__)
        except Exception as error:
            self._write_error(request_id, to_mcp_error(error)["code"], str(error))
            self._logger.exception("Handler '%s' raised an exception", method)
            return

        if isinstance(result, dict) and "error" in result:
            self._write_error(request_id, result["error"].get("code", "handler_error"), result["error"])
            self._logger.warning("Handler '%s' returned error payload", method)
            return

        if isinstance(result, Iterator):
            self._stream_response(request_id, result)
            return

        self._write_success(request_id, result)

    def _stream_response(self, request_id: Any, iterator: Iterator[Any]) -> None:
        for item in iterator:
            if isinstance(item, dict) and "error" in item:
                error_payload = item["error"]
                self._write_error(request_id, error_payload.get("code", "handler_error"), error_payload)
                self._logger.warning("Streaming handler yielded error payload for request %s", request_id)
                return
            self._write_success(request_id, item, partial=True)
            self._logger.debug("Streaming partial response for request %s", request_id)
        self._write_success(request_id, None, partial=False)
        self._logger.debug("Streaming handler completed for request %s", request_id)

    def _write_success(self, request_id: Any, result: Any, *, partial: bool = False) -> None:
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "result": result}
        if partial:
            payload["partial"] = True
        self._emit(payload, self._response_mode)

    def _write_error(self, request_id: Any, code: str, error: Any) -> None:
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error if isinstance(error, dict) else {"code": code, "message": str(error)},
        }
        if isinstance(error, dict):
            payload["error"].setdefault("code", code)
        self._emit(payload, self._response_mode)

    @staticmethod
    def _emit(payload: Dict[str, Any], mode: str) -> None:
        logger = get_logger("router")
        logger.debug("Sending response: %s", payload)

        if mode == "newline":
            sys.stdout.write(json.dumps(payload) + "\n")
            sys.stdout.flush()
            return

        data = json.dumps(payload).encode("utf-8")
        header = (
            f"Content-Length: {len(data)}\r\n"
            "Content-Type: application/json\r\n"
            "\r\n"
        ).encode("utf-8")
        sys.stdout.buffer.write(header)
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()


__all__ = ["Router"]
