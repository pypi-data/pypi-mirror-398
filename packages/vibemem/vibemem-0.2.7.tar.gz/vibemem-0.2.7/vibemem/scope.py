from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Optional, Sequence

Granularity = str  # "repo" | "cwd" | "path:N"


@dataclass(frozen=True)
class ScopeInfo:
    cwd: Path
    repo_root: Optional[Path]
    repo_slug: str
    rel_path: str
    scope_type: Literal["global", "project"]
    scope_id: str


REPO_ROOT_MARKERS: Sequence[str] = ("pyproject.toml", "package.json", "go.mod")


def find_repo_root(start: Path) -> Optional[Path]:
    start = start.resolve()
    candidates: Iterable[Path] = (start, *start.parents)

    for candidate in candidates:
        git_marker = candidate / ".git"
        if git_marker.exists():
            return candidate

    for candidate in candidates:
        for marker in REPO_ROOT_MARKERS:
            p = candidate / marker
            if marker.endswith("/") and p.is_dir():
                return candidate
            if p.exists():
                return candidate

    return None


def _safe_rel_path(repo_root: Path, cwd: Path) -> str:
    try:
        rel = cwd.resolve().relative_to(repo_root.resolve())
    except Exception:
        return ""
    if str(rel) == ".":
        return ""
    return rel.as_posix()


def _scope_id_for(rel_path: str, repo_slug: str, granularity: Granularity) -> str:
    if not repo_slug:
        return ""

    if rel_path == "":
        return repo_slug

    if granularity == "repo":
        return repo_slug

    if granularity == "cwd":
        return f"{repo_slug}::{rel_path}"

    if granularity.startswith("path:"):
        n_str = granularity.split(":", 1)[1]
        try:
            n = int(n_str)
        except ValueError:
            n = 0

        if n <= 0:
            return repo_slug

        parts = [p for p in rel_path.split("/") if p]
        prefix = "/".join(parts[:n])
        if prefix == "":
            return repo_slug
        return f"{repo_slug}::{prefix}"

    return repo_slug


def derive_scope(
    cwd: Path,
    *,
    repo_root_override: Optional[Path] = None,
    scope_type_override: Optional[Literal["global", "project"]] = None,
    scope_id_override: Optional[str] = None,
    granularity: Granularity = "repo",
) -> ScopeInfo:
    cwd = cwd.resolve()
    repo_root = repo_root_override.resolve() if repo_root_override else find_repo_root(cwd)

    repo_slug = repo_root.name if repo_root else ""
    rel_path = _safe_rel_path(repo_root, cwd) if repo_root else ""

    inferred_scope_type: Literal["global", "project"] = "project" if repo_root else "global"
    scope_type: Literal["global", "project"] = scope_type_override or inferred_scope_type

    if scope_type == "global":
        scope_id = scope_id_override or "global"
        return ScopeInfo(
            cwd=cwd,
            repo_root=repo_root,
            repo_slug=repo_slug,
            rel_path=rel_path,
            scope_type=scope_type,
            scope_id=scope_id,
        )

    # project scope
    if not repo_root:
        # explicit project scope without a repo root: treat cwd as pseudo-root.
        repo_root = cwd
        repo_slug = cwd.name
        rel_path = ""

    scope_id = scope_id_override or _scope_id_for(rel_path, repo_slug, granularity)

    return ScopeInfo(
        cwd=cwd,
        repo_root=repo_root,
        repo_slug=repo_slug,
        rel_path=rel_path,
        scope_type=scope_type,
        scope_id=scope_id,
    )


def scope_chain(scope: ScopeInfo, *, include_parents: bool = True) -> list[str]:
    if scope.scope_type != "project":
        return [scope.scope_id]

    if not include_parents:
        return [scope.scope_id]

    sid = scope.scope_id
    if "::" not in sid:
        return [sid]

    repo_slug, rest = sid.split("::", 1)
    repo_slug = repo_slug.strip()
    rest = rest.strip().strip("/")

    if not rest:
        return [repo_slug]

    parts = [p for p in rest.split("/") if p]
    chain: list[str] = []
    for i in range(len(parts), 0, -1):
        chain.append(f"{repo_slug}::{'/'.join(parts[:i])}")
    chain.append(repo_slug)
    return chain
