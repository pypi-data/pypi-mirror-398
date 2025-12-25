from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional, Sequence, Union

from vibemem.config import CacheMode, VibememConfig, load_config
from vibemem.models import Confidence, ListFilters, MemType, Memory, MemoryUpdate, PrincipalType, SearchHit, ScopeType
from vibemem.scope import Granularity, ScopeInfo, derive_scope, scope_chain
from vibemem.store.base import ConnectionError, SearchRequest
from vibemem.store.chroma_cache import ChromaCache, chroma_present_on_disk, default_chroma_path
from vibemem.store.weaviate_store import WeaviateStore
from vibemem.util import normalize_where_paths, parse_csv_list, uniq


CacheModeOpt = Literal["auto", "on", "off"]
TagsInput = Union[str, Sequence[str]]


@dataclass(frozen=True)
class SearchResult:
    query: str
    scope: ScopeInfo
    scope_type: str
    scope_ids: list[str]
    include_global: bool
    include_parents: bool
    used: Literal["weaviate", "chroma"]
    hits: list[SearchHit]


def _cache_enabled(mode: CacheModeOpt, scope: ScopeInfo) -> tuple[bool, Path]:
    path = default_chroma_path(scope)
    if mode == "off":
        return False, path
    if mode == "on":
        return True, path
    return chroma_present_on_disk(path), path


def _open_cache(mode: CacheModeOpt, scope: ScopeInfo) -> ChromaCache:
    enabled, path = _cache_enabled(mode, scope)
    try:
        return ChromaCache(path=path, enabled=enabled)
    except ModuleNotFoundError as e:
        if enabled:
            raise ModuleNotFoundError(
                "Chroma cache requested but 'chromadb' is not installed. "
                "Install with: python -m pip install -U 'vibemem[cache]'"
            ) from e
        return ChromaCache(path=path, enabled=False)


def _apply_specificity_boost(hits: Sequence[SearchHit], scope_ids: list[str]) -> list[SearchHit]:
    if not scope_ids:
        return list(hits)

    idx: dict[str, int] = {sid: i for i, sid in enumerate(scope_ids)}
    denom = max(len(scope_ids) - 1, 1)

    out: list[SearchHit] = []
    for hit in hits:
        base = float(hit.score or 0.0)

        boost = 0.0
        mem = hit.memory
        if mem.scope_type.value == "project" and mem.scope_id in idx:
            specificity = (denom - idx[mem.scope_id]) / float(denom)
            boost = 0.05 * specificity
        elif mem.scope_type.value == "global":
            boost = 0.01

        out.append(hit.model_copy(update={"score": base + boost}))

    out.sort(key=lambda h: float(h.score or 0.0), reverse=True)
    return out


def _dedupe_hits_by_id(hits: Sequence[SearchHit]) -> list[SearchHit]:
    out: list[SearchHit] = []
    seen: set[str] = set()
    for hit in hits:
        if hit.id in seen:
            continue
        seen.add(hit.id)
        out.append(hit)
    return out


def _normalize_tags(tags: Optional[TagsInput]) -> list[str]:
    if tags is None:
        return []
    if isinstance(tags, str):
        return uniq(parse_csv_list(tags))
    return uniq([str(t).strip() for t in tags if str(t).strip()])


class VibeMem:
    def __init__(
        self,
        *,
        cfg: Optional[VibememConfig] = None,
        cwd: Optional[Path] = None,
        repo_root: Optional[Path] = None,
        scope_type: Optional[Literal["global", "project"]] = None,
        scope_id: Optional[str] = None,
        granularity: Granularity = "repo",
    ) -> None:
        self.cfg = cfg or load_config()
        self._default_granularity = granularity
        self.scope = derive_scope(
            cwd or Path.cwd(),
            repo_root_override=repo_root,
            scope_type_override=scope_type,
            scope_id_override=scope_id,
            granularity=granularity,
        )

    def scope_info(self) -> ScopeInfo:
        return self.scope

    def _resolve_scope(
        self,
        *,
        scope: Optional[Literal["global", "project"]] = None,
        scope_id: Optional[str] = None,
        cwd: Optional[Path] = None,
        repo_root: Optional[Path] = None,
        granularity: Optional[Granularity] = None,
    ) -> ScopeInfo:
        effective_cwd = cwd or self.scope.cwd
        effective_repo_root = repo_root if repo_root is not None else self.scope.repo_root
        effective_granularity = granularity or self._default_granularity
        return derive_scope(
            effective_cwd,
            repo_root_override=effective_repo_root,
            scope_type_override=scope,
            scope_id_override=scope_id,
            granularity=effective_granularity,
        )

    @staticmethod
    def _repo_slug_for_scope_id(scope_id: str) -> str:
        sid = (scope_id or "").strip()
        if not sid:
            return ""
        if "::" in sid:
            return sid.split("::", 1)[0].strip()
        return sid

    def search(
        self,
        query: str,
        *,
        top: int = 8,
        include_global: bool = True,
        include_parents: bool = True,
        cache: CacheModeOpt = "auto",
        scope: Optional[Literal["global", "project"]] = None,
        scope_id: Optional[str] = None,
        scope_ids: Optional[Sequence[str]] = None,
        cwd: Optional[Path] = None,
        repo_root: Optional[Path] = None,
        granularity: Optional[Granularity] = None,
    ) -> SearchResult:
        effective_scope = self._resolve_scope(
            scope=scope,
            scope_id=scope_id,
            cwd=cwd,
            repo_root=repo_root,
            granularity=granularity,
        )

        effective_scope_ids: list[str]
        if scope_ids is not None:
            effective_scope_ids = [str(s).strip() for s in scope_ids if str(s).strip()]
        elif effective_scope.scope_type == "project":
            effective_scope_ids = scope_chain(effective_scope, include_parents=include_parents)
        else:
            effective_scope_ids = []
            include_global = False

        if effective_scope.scope_type != "project":
            include_global = False

        cache_mode: CacheMode = cache if cache != "auto" else self.cfg.cache_mode
        chroma = _open_cache(cache_mode, effective_scope)

        req = SearchRequest(
            query=query,
            scope_type=effective_scope.scope_type,
            scope_ids=effective_scope_ids,
            include_global=include_global,
            top_k=top,
        )

        used: Literal["weaviate", "chroma"] = "weaviate"
        try:
            store = WeaviateStore(self.cfg)
            try:
                hits = store.search(req)
            finally:
                store.close()
        except ConnectionError:
            if chroma.enabled():
                used = "chroma"
                hits = chroma.search(req)
            else:
                raise

        boosted = _apply_specificity_boost(hits, effective_scope_ids)
        deduped = _dedupe_hits_by_id(boosted)[:top]

        return SearchResult(
            query=query,
            scope=effective_scope,
            scope_type=effective_scope.scope_type,
            scope_ids=effective_scope_ids,
            include_global=include_global,
            include_parents=include_parents,
            used=used,
            hits=deduped,
        )

    def search_hits(self, query: str, **kwargs: object) -> list[SearchHit]:
        return self.search(query, **kwargs).hits

    def search_memories(self, query: str, **kwargs: object) -> list[Memory]:
        return [h.memory for h in self.search(query, **kwargs).hits]

    def add_memory(
        self,
        *,
        mem_type: Union[MemType, str],
        text: str,
        tags: Optional[TagsInput] = None,
        principal_type: Optional[Union[PrincipalType, str]] = None,
        principal_id: Optional[str] = None,
        bot_id: Optional[str] = None,
        confidence: Union[Confidence, str] = Confidence.med,
        verification: Optional[str] = None,
        errors: Optional[Sequence[str]] = None,
        files: Optional[Sequence[str]] = None,
        commands_run: Optional[Sequence[str]] = None,
        cache: CacheModeOpt = "auto",
        scope: Optional[Literal["global", "project"]] = None,
        scope_id: Optional[str] = None,
        cwd: Optional[Path] = None,
        repo_root: Optional[Path] = None,
        granularity: Optional[Granularity] = None,
    ) -> Memory:
        effective_scope = self._resolve_scope(
            scope=scope,
            scope_id=scope_id,
            cwd=cwd,
            repo_root=repo_root,
            granularity=granularity,
        )

        cache_mode: CacheMode = cache if cache != "auto" else self.cfg.cache_mode
        chroma = _open_cache(cache_mode, effective_scope)

        repo_slug = effective_scope.repo_slug
        rel_path = effective_scope.rel_path
        if effective_scope.scope_type == "project" and scope_id is not None:
            repo_slug = self._repo_slug_for_scope_id(scope_id) or repo_slug
            rel_path = ""
            if "::" in scope_id:
                rel_path = scope_id.split("::", 1)[1].strip().strip("/")

        extra: dict[str, object] = {}

        if principal_type is not None:
            extra["principal_type"] = PrincipalType(principal_type)
        elif self.cfg.principal_type is not None:
            extra["principal_type"] = self.cfg.principal_type
        if principal_id is not None:
            extra["principal_id"] = principal_id
        elif self.cfg.principal_id is not None:
            extra["principal_id"] = self.cfg.principal_id
        if bot_id is not None:
            extra["bot_id"] = bot_id

        m = Memory(
            text=text,
            mem_type=MemType(mem_type),
            tags=_normalize_tags(tags),
            scope_type=ScopeType(effective_scope.scope_type),
            scope_id=effective_scope.scope_id,
            repo=repo_slug,
            rel_path=rel_path,
            confidence=Confidence(confidence),
            verification=verification,
            error_signatures=list(errors) if errors else None,
            files=normalize_where_paths(files or []) or None,
            commands_run=list(commands_run) if commands_run else None,
            **extra,
        )

        store = WeaviateStore(self.cfg)
        try:
            created = store.add(m)
        finally:
            store.close()

        if chroma.enabled():
            chroma.upsert(created)

        return created

    def edit_memory(
        self,
        memory_id: str,
        *,
        text: Optional[str] = None,
        mem_type: Optional[Union[MemType, str]] = None,
        tags: Optional[TagsInput] = None,
        principal_type: Optional[Union[PrincipalType, str]] = None,
        principal_id: Optional[str] = None,
        bot_id: Optional[str] = None,
        confidence: Optional[Union[Confidence, str]] = None,
        verification: Optional[str] = None,
        cache: CacheModeOpt = "auto",
        scope: Optional[Literal["global", "project"]] = None,
        scope_id: Optional[str] = None,
        cwd: Optional[Path] = None,
        repo_root: Optional[Path] = None,
        granularity: Optional[Granularity] = None,
    ) -> Memory:
        effective_scope = self._resolve_scope(
            scope=scope,
            scope_id=scope_id,
            cwd=cwd,
            repo_root=repo_root,
            granularity=granularity,
        )
        cache_mode: CacheMode = cache if cache != "auto" else self.cfg.cache_mode
        chroma = _open_cache(cache_mode, effective_scope)

        upd = MemoryUpdate(
            text=text,
            mem_type=MemType(mem_type) if mem_type is not None else None,
            tags=_normalize_tags(tags) if tags is not None else None,
            principal_type=PrincipalType(principal_type) if principal_type is not None else None,
            principal_id=principal_id,
            bot_id=bot_id,
            confidence=Confidence(confidence) if confidence is not None else None,
            verification=verification,
        )

        store = WeaviateStore(self.cfg)
        try:
            updated = store.edit(memory_id, upd)
        finally:
            store.close()

        if chroma.enabled():
            chroma.upsert(updated)

        return updated

    def delete_memory(
        self,
        memory_id: str,
        *,
        cache: CacheModeOpt = "auto",
        scope: Optional[Literal["global", "project"]] = None,
        scope_id: Optional[str] = None,
        cwd: Optional[Path] = None,
        repo_root: Optional[Path] = None,
        granularity: Optional[Granularity] = None,
    ) -> None:
        effective_scope = self._resolve_scope(
            scope=scope,
            scope_id=scope_id,
            cwd=cwd,
            repo_root=repo_root,
            granularity=granularity,
        )
        cache_mode: CacheMode = cache if cache != "auto" else self.cfg.cache_mode
        chroma = _open_cache(cache_mode, effective_scope)

        store = WeaviateStore(self.cfg)
        try:
            store.delete(memory_id)
        finally:
            store.close()

        if chroma.enabled():
            chroma.delete(memory_id)

    def get_memory(self, memory_id: str) -> Memory:
        store = WeaviateStore(self.cfg)
        try:
            return store.get(memory_id)
        finally:
            store.close()

    def list_memories(
        self,
        *,
        scope: Literal["global", "project", "all"] = "project",
        mem_type: Optional[Union[MemType, str]] = None,
        tag: Optional[str] = None,
        limit: int = 20,
        repo: Optional[str] = None,
        scope_ids: Optional[Sequence[str]] = None,
    ) -> list[Memory]:
        scope = scope.strip().lower()
        if scope not in ("global", "project", "all"):
            raise ValueError("scope must be 'global', 'project', or 'all'")

        effective_repo = repo
        if effective_repo is None and scope == "project" and self.scope.repo_slug:
            effective_repo = self.scope.repo_slug

        effective_scope_ids = list(scope_ids) if scope_ids is not None else None

        filters = ListFilters(
            scope=scope,
            mem_type=MemType(mem_type) if isinstance(mem_type, str) else mem_type,
            tag=(tag.strip() if tag else None),
            limit=limit,
            repo=effective_repo,
            scope_ids=effective_scope_ids,
        )

        store = WeaviateStore(self.cfg)
        try:
            return store.list(filters)
        finally:
            store.close()

    def sync_pull(self, *, limit: int = 200) -> dict[str, object]:
        if self.scope.scope_type != "project":
            raise ValueError("sync_pull requires project scope (run inside a repo or set scope_type='project').")

        chroma = _open_cache("on", self.scope)
        if not chroma.enabled():
            raise ModuleNotFoundError(
                "Chroma cache requested but 'chromadb' is not installed. "
                "Install with: python -m pip install -U 'vibemem[cache]'"
            )

        scope_ids = scope_chain(self.scope, include_parents=True)

        store = WeaviateStore(self.cfg)
        try:
            memories = store.list(
                ListFilters(
                    scope="project",
                    mem_type=None,
                    tag=None,
                    limit=limit,
                    repo=self.scope.repo_slug,
                    scope_ids=scope_ids,
                )
            )
        finally:
            store.close()

        chroma.rebuild(memories)
        return {
            "pulled": len(memories),
            "scope_ids": scope_ids,
            "chroma_path": str(default_chroma_path(self.scope)),
            "chroma_count": chroma.count(),
        }


def scope_info(
    *,
    cfg: Optional[VibememConfig] = None,
    cwd: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    scope_type: Optional[Literal["global", "project"]] = None,
    scope_id: Optional[str] = None,
    granularity: Granularity = "repo",
) -> ScopeInfo:
    return VibeMem(
        cfg=cfg,
        cwd=cwd,
        repo_root=repo_root,
        scope_type=scope_type,
        scope_id=scope_id,
        granularity=granularity,
    ).scope_info()


def search(
    query: str,
    *,
    top: int = 8,
    include_global: bool = True,
    include_parents: bool = True,
    cache: CacheModeOpt = "auto",
    cfg: Optional[VibememConfig] = None,
    cwd: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    scope_type: Optional[Literal["global", "project"]] = None,
    scope_id: Optional[str] = None,
    granularity: Granularity = "repo",
) -> SearchResult:
    return VibeMem(
        cfg=cfg,
        cwd=cwd,
        repo_root=repo_root,
        scope_type=scope_type,
        scope_id=scope_id,
        granularity=granularity,
    ).search(
        query,
        top=top,
        include_global=include_global,
        include_parents=include_parents,
        cache=cache,
    )


def search_hits(
    query: str,
    *,
    top: int = 8,
    include_global: bool = True,
    include_parents: bool = True,
    cache: CacheModeOpt = "auto",
    cfg: Optional[VibememConfig] = None,
    cwd: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    scope_type: Optional[Literal["global", "project"]] = None,
    scope_id: Optional[str] = None,
    granularity: Granularity = "repo",
) -> list[SearchHit]:
    return search(
        query,
        top=top,
        include_global=include_global,
        include_parents=include_parents,
        cache=cache,
        cfg=cfg,
        cwd=cwd,
        repo_root=repo_root,
        scope_type=scope_type,
        scope_id=scope_id,
        granularity=granularity,
    ).hits


def search_memories(
    query: str,
    *,
    top: int = 8,
    include_global: bool = True,
    include_parents: bool = True,
    cache: CacheModeOpt = "auto",
    cfg: Optional[VibememConfig] = None,
    cwd: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    scope_type: Optional[Literal["global", "project"]] = None,
    scope_id: Optional[str] = None,
    granularity: Granularity = "repo",
) -> list[Memory]:
    return [
        h.memory
        for h in search_hits(
        query,
        top=top,
        include_global=include_global,
        include_parents=include_parents,
        cache=cache,
        cfg=cfg,
        cwd=cwd,
        repo_root=repo_root,
        scope_type=scope_type,
        scope_id=scope_id,
        granularity=granularity,
    )
    ]


def add_memory(
    *,
    mem_type: Union[MemType, str],
    text: str,
    tags: Optional[TagsInput] = None,
    principal_type: Optional[Union[PrincipalType, str]] = None,
    principal_id: Optional[str] = None,
    bot_id: Optional[str] = None,
    confidence: Union[Confidence, str] = Confidence.med,
    verification: Optional[str] = None,
    errors: Optional[Sequence[str]] = None,
    files: Optional[Sequence[str]] = None,
    commands_run: Optional[Sequence[str]] = None,
    cache: CacheModeOpt = "auto",
    cfg: Optional[VibememConfig] = None,
    cwd: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    scope_type: Optional[Literal["global", "project"]] = None,
    scope_id: Optional[str] = None,
    granularity: Granularity = "repo",
) -> Memory:
    return VibeMem(
        cfg=cfg,
        cwd=cwd,
        repo_root=repo_root,
        scope_type=scope_type,
        scope_id=scope_id,
        granularity=granularity,
    ).add_memory(
        mem_type=mem_type,
        text=text,
        tags=tags,
        principal_type=principal_type,
        principal_id=principal_id,
        bot_id=bot_id,
        confidence=confidence,
        verification=verification,
        errors=errors,
        files=files,
        commands_run=commands_run,
        cache=cache,
    )


def edit_memory(
    memory_id: str,
    *,
    text: Optional[str] = None,
    mem_type: Optional[Union[MemType, str]] = None,
    tags: Optional[TagsInput] = None,
    principal_type: Optional[Union[PrincipalType, str]] = None,
    principal_id: Optional[str] = None,
    bot_id: Optional[str] = None,
    confidence: Optional[Union[Confidence, str]] = None,
    verification: Optional[str] = None,
    cache: CacheModeOpt = "auto",
    cfg: Optional[VibememConfig] = None,
    cwd: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    scope_type: Optional[Literal["global", "project"]] = None,
    scope_id: Optional[str] = None,
    granularity: Granularity = "repo",
) -> Memory:
    return VibeMem(
        cfg=cfg,
        cwd=cwd,
        repo_root=repo_root,
        scope_type=scope_type,
        scope_id=scope_id,
        granularity=granularity,
    ).edit_memory(
        memory_id,
        text=text,
        mem_type=mem_type,
        tags=tags,
        principal_type=principal_type,
        principal_id=principal_id,
        bot_id=bot_id,
        confidence=confidence,
        verification=verification,
        cache=cache,
    )


def delete_memory(
    memory_id: str,
    *,
    cache: CacheModeOpt = "auto",
    cfg: Optional[VibememConfig] = None,
    cwd: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    scope_type: Optional[Literal["global", "project"]] = None,
    scope_id: Optional[str] = None,
    granularity: Granularity = "repo",
) -> None:
    VibeMem(
        cfg=cfg,
        cwd=cwd,
        repo_root=repo_root,
        scope_type=scope_type,
        scope_id=scope_id,
        granularity=granularity,
    ).delete_memory(memory_id, cache=cache)


def get_memory(
    memory_id: str,
    *,
    cfg: Optional[VibememConfig] = None,
    cwd: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    scope_type: Optional[Literal["global", "project"]] = None,
    scope_id: Optional[str] = None,
    granularity: Granularity = "repo",
) -> Memory:
    return VibeMem(
        cfg=cfg,
        cwd=cwd,
        repo_root=repo_root,
        scope_type=scope_type,
        scope_id=scope_id,
        granularity=granularity,
    ).get_memory(memory_id)


def list_memories(
    *,
    scope: Literal["global", "project", "all"] = "project",
    mem_type: Optional[Union[MemType, str]] = None,
    tag: Optional[str] = None,
    limit: int = 20,
    repo: Optional[str] = None,
    scope_ids: Optional[Sequence[str]] = None,
    cfg: Optional[VibememConfig] = None,
    cwd: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    scope_type: Optional[Literal["global", "project"]] = None,
    scope_id: Optional[str] = None,
    granularity: Granularity = "repo",
) -> list[Memory]:
    return VibeMem(
        cfg=cfg,
        cwd=cwd,
        repo_root=repo_root,
        scope_type=scope_type,
        scope_id=scope_id,
        granularity=granularity,
    ).list_memories(
        scope=scope,
        mem_type=mem_type,
        tag=tag,
        limit=limit,
        repo=repo,
        scope_ids=scope_ids,
    )


def sync_pull(
    *,
    limit: int = 200,
    cfg: Optional[VibememConfig] = None,
    cwd: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    scope_type: Optional[Literal["global", "project"]] = None,
    scope_id: Optional[str] = None,
    granularity: Granularity = "repo",
) -> dict[str, object]:
    return VibeMem(
        cfg=cfg,
        cwd=cwd,
        repo_root=repo_root,
        scope_type=scope_type,
        scope_id=scope_id,
        granularity=granularity,
    ).sync_pull(limit=limit)
