from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Sequence

from vibemem.models import ListFilters, Memory, MemoryUpdate, SearchHit


class VibememError(Exception):
    pass


class ConfigError(VibememError):
    pass


class ConnectionError(VibememError):
    pass


class NotFoundError(VibememError):
    pass


@dataclass(frozen=True)
class SearchRequest:
    query: str
    scope_type: str  # "global" | "project"
    scope_ids: Sequence[str]
    include_global: bool
    top_k: int = 8


class MemoryStore(Protocol):
    def add(self, memory: Memory) -> Memory: ...

    def get(self, memory_id: str) -> Memory: ...

    def edit(self, memory_id: str, update: MemoryUpdate) -> Memory: ...

    def delete(self, memory_id: str) -> None: ...

    def search(self, req: SearchRequest) -> list[SearchHit]: ...

    def list(self, filters: ListFilters) -> list[Memory]: ...


class MemoryCache(Protocol):
    def enabled(self) -> bool: ...

    def upsert(self, memory: Memory) -> None: ...

    def delete(self, memory_id: str) -> None: ...

    def search(self, req: SearchRequest) -> list[SearchHit]: ...

    def rebuild(self, memories: Sequence[Memory]) -> None: ...

    def count(self) -> Optional[int]: ...