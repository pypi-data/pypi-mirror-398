from __future__ import annotations

from pathlib import Path

import pytest

from vibemem.scope import derive_scope, scope_chain


def test_derive_scope_finds_git_root(tmp_path: Path) -> None:
    repo = tmp_path / "myrepo"
    (repo / ".git").mkdir(parents=True)
    sub = repo / "services" / "api"
    sub.mkdir(parents=True)

    s = derive_scope(sub)

    assert s.repo_root == repo
    assert s.repo_slug == "myrepo"
    assert s.rel_path == "services/api"
    assert s.scope_type == "project"
    assert s.scope_id == "myrepo"


def test_derive_scope_granularity_cwd(tmp_path: Path) -> None:
    repo = tmp_path / "myrepo"
    (repo / ".git").mkdir(parents=True)
    sub = repo / "services" / "api"
    sub.mkdir(parents=True)

    s = derive_scope(sub, granularity="cwd")
    assert s.scope_id == "myrepo::services/api"


def test_derive_scope_granularity_path_n(tmp_path: Path) -> None:
    repo = tmp_path / "myrepo"
    (repo / ".git").mkdir(parents=True)
    sub = repo / "services" / "api" / "v1"
    sub.mkdir(parents=True)

    s1 = derive_scope(sub, granularity="path:1")
    assert s1.scope_id == "myrepo::services"

    s2 = derive_scope(sub, granularity="path:2")
    assert s2.scope_id == "myrepo::services/api"

    s0 = derive_scope(sub, granularity="path:0")
    assert s0.scope_id == "myrepo"


def test_scope_chain_bubbles_up_from_scope_id(tmp_path: Path) -> None:
    repo = tmp_path / "myrepo"
    (repo / ".git").mkdir(parents=True)
    sub = repo / "a" / "b" / "c"
    sub.mkdir(parents=True)

    s = derive_scope(sub, granularity="cwd")
    assert s.scope_id == "myrepo::a/b/c"

    chain = scope_chain(s, include_parents=True)
    assert chain == ["myrepo::a/b/c", "myrepo::a/b", "myrepo::a", "myrepo"]


def test_outside_repo_defaults_to_global(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir(parents=True)

    s = derive_scope(outside)
    assert s.scope_type == "global"
    assert s.scope_id == "global"
    assert s.repo_root is None