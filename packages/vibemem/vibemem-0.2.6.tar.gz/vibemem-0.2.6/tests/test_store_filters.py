from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from vibemem.store.base import SearchRequest
import vibemem.store.weaviate_store as ws


@dataclass(frozen=True)
class FakeFilter:
    op: str
    value: Any

    @classmethod
    def by_property(cls, name: str) -> "FakeFilter":
        return cls("prop", name)

    def equal(self, value: Any) -> "FakeFilter":
        assert self.op == "prop"
        return FakeFilter("eq", (self.value, value))

    @classmethod
    def all_of(cls, filters: list["FakeFilter"]) -> "FakeFilter":
        return cls("all", tuple(filters))

    @classmethod
    def any_of(cls, filters: list["FakeFilter"]) -> "FakeFilter":
        return cls("any", tuple(filters))


class StubQuery:
    def __init__(self) -> None:
        self.last_kwargs: dict[str, Any] = {}
        self.hybrid_calls = 0

    def hybrid(self, *args: Any, **kwargs: Any) -> Any:
        self.hybrid_calls += 1
        self.last_kwargs = dict(kwargs)
        return SimpleNamespace(objects=[])

    def bm25(self, *args: Any, **kwargs: Any) -> Any:
        self.last_kwargs = dict(kwargs)
        return SimpleNamespace(objects=[])


class StubQueryHybridNoVectorizer(StubQuery):
    def hybrid(self, *args: Any, **kwargs: Any) -> Any:
        self.hybrid_calls += 1
        raise RuntimeError("VectorFromInput was called without vectorizer on class VibeMemMemory")


def _make_store(query: StubQuery) -> ws.WeaviateStore:
    store = object.__new__(ws.WeaviateStore)
    store._collection = SimpleNamespace(query=query)
    return store


def test_weaviate_search_filter_includes_global(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ws.wfilters, "Filter", FakeFilter)

    q = StubQuery()
    store = _make_store(q)

    req = SearchRequest(
        query="hello",
        scope_type="project",
        scope_ids=["repo::a", "repo"],
        include_global=True,
        top_k=5,
    )
    store.search(req)

    got = q.last_kwargs["filters"]
    expected = FakeFilter.any_of(
        [
            FakeFilter.all_of(
                [
                    FakeFilter.by_property("scope_type").equal("project"),
                    FakeFilter.any_of(
                        [
                            FakeFilter.by_property("scope_id").equal("repo::a"),
                            FakeFilter.by_property("scope_id").equal("repo"),
                        ]
                    ),
                ]
            ),
            FakeFilter.by_property("scope_type").equal("global"),
        ]
    )
    assert got == expected


def test_weaviate_search_filter_global_does_not_or_global(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ws.wfilters, "Filter", FakeFilter)

    q = StubQuery()
    store = _make_store(q)

    req = SearchRequest(
        query="hello",
        scope_type="global",
        scope_ids=[],
        include_global=True,
        top_k=5,
    )
    store.search(req)

    got = q.last_kwargs["filters"]
    assert got == FakeFilter.by_property("scope_type").equal("global")


def test_weaviate_search_falls_back_to_bm25_when_no_vectorizer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ws.wfilters, "Filter", FakeFilter)

    q = StubQueryHybridNoVectorizer()
    store = _make_store(q)

    req = SearchRequest(
        query="hello",
        scope_type="project",
        scope_ids=["repo::a", "repo"],
        include_global=True,
        top_k=5,
    )
    store.search(req)

    assert q.hybrid_calls >= 1
    got = q.last_kwargs["filters"]
    expected = FakeFilter.any_of(
        [
            FakeFilter.all_of(
                [
                    FakeFilter.by_property("scope_type").equal("project"),
                    FakeFilter.any_of(
                        [
                            FakeFilter.by_property("scope_id").equal("repo::a"),
                            FakeFilter.by_property("scope_id").equal("repo"),
                        ]
                    ),
                ]
            ),
            FakeFilter.by_property("scope_type").equal("global"),
        ]
    )
    assert got == expected


def test_weaviate_search_uses_query_vector_when_embedder_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ws.wfilters, "Filter", FakeFilter)

    class StubEmbedder:
        def embed(self, texts: list[str]) -> list[list[float]]:
            assert texts == ["hello"]
            return [[0.1, 0.2, 0.3]]

    q = StubQuery()
    store = _make_store(q)
    store._embedder = StubEmbedder()  # type: ignore[attr-defined]

    req = SearchRequest(query="hello", scope_type="global", scope_ids=[], include_global=False, top_k=5)
    store.search(req)

    assert "vector" in q.last_kwargs
    assert q.last_kwargs["vector"] == [0.1, 0.2, 0.3]
