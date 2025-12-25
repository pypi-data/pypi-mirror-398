from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import vibemem.api as api
from vibemem.config import VibememConfig
from vibemem.models import MemType, Memory, ScopeType, SearchHit


def test_search_passes_scope_chain_into_request(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "myrepo"
    (repo_root / ".git").mkdir(parents=True)
    cwd = repo_root / "a" / "b"
    cwd.mkdir(parents=True)

    captured: dict[str, Any] = {}

    class StubStore:
        def __init__(self, cfg: VibememConfig) -> None:
            self._cfg = cfg

        def search(self, req: api.SearchRequest) -> list[SearchHit]:
            captured["req"] = req
            return []

        def close(self) -> None:
            captured["closed"] = True

    monkeypatch.setattr(api, "WeaviateStore", StubStore)

    vm = api.VibeMem(
        cfg=VibememConfig(weaviate_url="http://example:8080"),
        cwd=cwd,
        repo_root=repo_root,
        granularity="cwd",
    )
    result = vm.search("hello", cache="off", include_parents=True)

    req = captured["req"]
    assert req.scope_type == "project"
    assert list(req.scope_ids) == ["myrepo::a/b", "myrepo::a", "myrepo"]
    assert captured["closed"] is True
    assert result.scope_ids == ["myrepo::a/b", "myrepo::a", "myrepo"]
    assert result.scope.scope_id == "myrepo::a/b"


def test_search_falls_back_to_chroma_when_weaviate_unreachable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / ".git").mkdir(parents=True)

    class StubChroma:
        def __init__(self, *, path: Path, enabled: bool) -> None:
            self._enabled = enabled

        def enabled(self) -> bool:
            return self._enabled

        def search(self, req: api.SearchRequest) -> list[SearchHit]:
            mem = Memory(
                text="cached memory",
                mem_type=MemType.finding,
                tags=[],
                scope_type=ScopeType.project,
                scope_id=req.scope_ids[0] if req.scope_ids else "repo",
                repo="repo",
                rel_path="",
            )
            return [SearchHit(id="1", score=0.5, memory=mem, source="chroma")]

    monkeypatch.setattr(api, "ChromaCache", StubChroma)

    vm = api.VibeMem(cfg=VibememConfig(weaviate_url=None), cwd=repo_root, repo_root=repo_root)
    result = vm.search("hello", cache="on")

    assert result.used == "chroma"
    assert [h.id for h in result.hits] == ["1"]
    assert result.scope.scope_type == "project"


def test_scope_info_matches_derived_scope(tmp_path: Path) -> None:
    repo_root = tmp_path / "myrepo"
    (repo_root / ".git").mkdir(parents=True)
    cwd = repo_root / "x"
    cwd.mkdir(parents=True)

    s = api.scope_info(cfg=VibememConfig(weaviate_url="http://example:8080"), cwd=cwd, repo_root=repo_root, granularity="cwd")
    assert s.scope_type == "project"
    assert s.scope_id == "myrepo::x"


def test_add_memory_can_target_global_scope(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "myrepo"
    (repo_root / ".git").mkdir(parents=True)
    cwd = repo_root / "subdir"
    cwd.mkdir(parents=True)

    captured: dict[str, Any] = {}

    class StubStore:
        def __init__(self, cfg: VibememConfig) -> None:
            self._cfg = cfg

        def add(self, memory: Memory) -> Memory:
            captured["memory"] = memory
            return memory

        def close(self) -> None:
            return

    monkeypatch.setattr(api, "WeaviateStore", StubStore)

    vm = api.VibeMem(cfg=VibememConfig(weaviate_url=None), cwd=cwd, repo_root=repo_root)
    created = vm.add_memory(mem_type="recipe", scope="global", text="Use X", tags=["python"], cache="off")

    assert created.scope_type == ScopeType.global_
    assert created.scope_id == "global"
    assert created.repo == "myrepo"
    assert captured["memory"].scope_type == ScopeType.global_


def test_add_memory_allows_explicit_project_scope_id(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class StubStore:
        def __init__(self, cfg: VibememConfig) -> None:
            self._cfg = cfg

        def add(self, memory: Memory) -> Memory:
            captured["memory"] = memory
            return memory

        def close(self) -> None:
            return

    monkeypatch.setattr(api, "WeaviateStore", StubStore)

    vm = api.VibeMem(cfg=VibememConfig(weaviate_url=None))
    created = vm.add_memory(
        mem_type="recipe",
        scope="project",
        scope_id="otherrepo::a/b",
        text="Use X",
        tags="python",
        cache="off",
    )

    assert created.scope_type == ScopeType.project
    assert created.scope_id == "otherrepo::a/b"
    assert created.repo == "otherrepo"
    assert created.rel_path == "a/b"
    assert captured["memory"].repo == "otherrepo"
