from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
import uuid


class DataStore(Protocol):
    """Stores full tool outputs out-of-band and returns a handle (data_key).

    The LLM should only ever receive the handle + a bounded preview.
    """

    def put(self, value: Any) -> str: ...

    def get(self, data_key: str) -> Any: ...

    def delete(self, data_key: str) -> None: ...


@dataclass
class InMemoryDataStore:
    """Simple in-memory DataStore for testing/dev."""

    _values: dict[str, Any]

    def __init__(self) -> None:
        self._values = {}

    def put(self, value: Any) -> str:
        data_key = f"mem://{uuid.uuid4()}"
        self._values[data_key] = value
        return data_key

    def get(self, data_key: str) -> Any:
        return self._values[data_key]

    def delete(self, data_key: str) -> None:
        self._values.pop(data_key, None)
