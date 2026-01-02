from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator


class DummyModel:
    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

    def model_dump(self) -> Dict[str, Any]:
        return dict(self._data)


class FactoryStub:
    def __init__(self, client: Any) -> None:
        self._client = client

    @contextmanager
    def build_sync_client(self, prompt: Any) -> Iterator[Any]:
        yield self._client
