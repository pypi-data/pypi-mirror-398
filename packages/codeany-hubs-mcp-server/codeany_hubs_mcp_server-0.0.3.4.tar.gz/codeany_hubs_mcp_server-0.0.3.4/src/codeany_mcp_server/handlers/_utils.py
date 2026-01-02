"""Shared helper functions for handler modules."""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping, TypeVar

T = TypeVar("T")

def to_payload(value: Any) -> Any:
    """Convert Pydantic models or dataclasses to plain Python structures."""

    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    if hasattr(value, "__dataclass_fields__"):
        dataclass_fields = getattr(value, "__dataclass_fields__")
        return {field: getattr(value, field) for field in dataclass_fields}
    return value


def to_payload_list(values: Iterable[Any]) -> List[Any]:
    return [to_payload(item) for item in values]


def require_confirm(params: Mapping[str, Any]) -> bool:
    """
    Determine whether a destructive operation has explicit confirmation.

    Convention: params may include boolean `confirm`. False or missing requires
    a consent prompt.
    """

    return bool(params.get("confirm", False))


def require_param(params: Mapping[str, T], name: str) -> T:
    try:
        return params[name]
    except KeyError as exc:
        raise ValueError(f"Missing required parameter '{name}'.") from exc


__all__ = ["to_payload", "to_payload_list", "require_confirm", "require_param"]
