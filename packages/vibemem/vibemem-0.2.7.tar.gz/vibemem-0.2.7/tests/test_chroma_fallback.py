from __future__ import annotations

from typing import Any

from vibemem.store.base import SearchRequest
from vibemem.store.chroma_cache import ChromaCache


class StubCollection:
    def __init__(self, *, ids: list[str], documents: list[str], metadatas: list[dict[str, Any]]) -> None:
        self._ids = ids
        self._documents = documents
        self._metadatas = metadatas
        self.query_calls = 0
        self.get_calls = 0

    def query(self, *args: Any, **kwargs: Any) -> Any:
        self.query_calls += 1
        raise RuntimeError("query failed")

    def get(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.get_calls += 1
        return {"ids": list(self._ids), "documents": list(self._documents), "metadatas": list(self._metadatas)}


def _meta(*, scope_type: str, scope_id: str) -> dict[str, Any]:
    return {
        "mem_type": "finding",
        "tags_csv": "",
        "scope_type": scope_type,
        "scope_id": scope_id,
        "repo": "repo",
        "rel_path": "",
        "confidence": "med",
        "verification": "",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00",
        "error_signatures_json": "[]",
        "files_json": "[]",
        "commands_run_json": "[]",
    }


def test_chroma_search_falls_back_to_scan_when_query_fails() -> None:
    collection = StubCollection(
        ids=["1", "2", "3"],
        documents=["foo bar", "foo baz", "foo foo"],
        metadatas=[
            _meta(scope_type="project", scope_id="repo::a"),
            _meta(scope_type="project", scope_id="repo::other"),
            _meta(scope_type="global", scope_id="global"),
        ],
    )

    cache = object.__new__(ChromaCache)
    cache._enabled = True
    cache._collection = collection

    req = SearchRequest(
        query="foo bar",
        scope_type="project",
        scope_ids=["repo::a", "repo"],
        include_global=True,
        top_k=10,
    )
    hits = cache.search(req)

    assert collection.query_calls >= 1
    assert collection.get_calls >= 1
    assert [h.id for h in hits] == ["1", "3"]

