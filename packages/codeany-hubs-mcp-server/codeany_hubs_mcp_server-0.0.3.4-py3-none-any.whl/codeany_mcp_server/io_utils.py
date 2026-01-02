"""Input/output helpers for MCP handlers."""

from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import Any, MutableMapping, Optional, Tuple, Union

FileTuple = Union[Tuple[str, bytes], Tuple[str, bytes, str]]


def coerce_bytes_or_path(value: Any, *, allow_paths: bool) -> bytes:
    """
    Convert various input payloads into raw bytes.

    Accepts raw bytes/bytearray, file-like objects, data URIs, or local file paths
    (when `allow_paths=True`). Raises a ValueError when conversion fails.
    """

    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)

    if hasattr(value, "read"):
        data = value.read()
        if isinstance(data, str):
            data = data.encode("utf-8")
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("File-like objects must return bytes.")
        return bytes(data)

    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("data:"):
            return _decode_data_uri(stripped)
        if allow_paths:
            return _read_local_path(stripped)
        raise ValueError("Local file paths are disabled by configuration.")

    raise ValueError("Unsupported payload type for binary conversion.")


def enforce_size_limit(data: bytes, max_mb: int) -> None:
    """Ensure the payload does not exceed the configured limit."""

    limit = max_mb * 1024 * 1024
    if len(data) > limit:
        raise ValueError(f"Payload exceeds maximum allowed size of {max_mb} MB.")


def files_tuple(
    field: str,
    data: bytes,
    *,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
) -> MutableMapping[str, FileTuple]:
    """Build an `httpx`-compatible files mapping."""

    file_name = filename or field
    value: FileTuple = (file_name, data, content_type) if content_type else (file_name, data)
    return {field: value}


def _decode_data_uri(value: str) -> bytes:
    header, _, payload = value.partition(",")
    if not payload:
        raise ValueError("Malformed data URI payload.")

    is_base64 = ";base64" in header
    if not is_base64:
        return payload.encode("utf-8")

    try:
        return base64.b64decode(payload, validate=True)
    except binascii.Error as exc:  # pragma: no cover - depends on malformed inputs
        raise ValueError("Invalid base64 payload in data URI.") from exc


def _read_local_path(raw_path: str) -> bytes:
    path = Path(raw_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_bytes()


__all__ = ["coerce_bytes_or_path", "enforce_size_limit", "files_tuple"]
