from __future__ import annotations

import importlib
import json
import hashlib
import math
import re
from pathlib import Path
from typing import Any, Optional, Sequence

from vibemem.models import Memory, SearchHit, memory_from_properties
from vibemem.scope import ScopeInfo
from vibemem.store.base import MemoryCache, SearchRequest
from vibemem.util import simple_text_score


_WORD_RE = re.compile(r"[A-Za-z0-9_]+")


def default_chroma_path(scope: ScopeInfo) -> Path:
    base = Path.home() / ".vibemem" / "chroma"
    if scope.repo_root:
        try:
            root = scope.repo_root.resolve()
        except Exception:
            root = scope.repo_root
        digest = hashlib.sha1(str(root).encode("utf-8")).hexdigest()[:10]
        slug = scope.repo_slug or "repo"
        return base / f"{slug}-{digest}"
    return base / "global"


def chroma_present_on_disk(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_file():
        return False
    try:
        return any(path.iterdir())
    except Exception:
        return False


def _hash_embedding(text: str, *, dim: int = 256) -> list[float]:
    # Deterministic, dependency-free embedding for offline cache usage.
    # Not meant to be SOTA; just stable and "good enough" for small local caches.
    vec = [0.0] * dim
    tokens = [t.lower() for t in _WORD_RE.findall(text)]
    if not tokens:
        return vec

    for t in tokens:
        h = 2166136261
        for ch in t:
            h ^= ord(ch)
            h *= 16777619
            h &= 0xFFFFFFFF
        idx = h % dim
        sign = -1.0 if (h & 1) else 1.0
        vec[idx] += sign * 1.0

    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _memory_to_chroma_metadata(memory: Memory) -> dict[str, Any]:
    return {
        "mem_type": memory.mem_type.value,
        "tags_csv": ",".join(memory.tags),
        "principal_type": memory.principal_type.value,
        "principal_id": memory.principal_id,
        "bot_id": memory.bot_id or "",
        "scope_type": memory.scope_type.value,
        "scope_id": memory.scope_id,
        "repo": memory.repo,
        "rel_path": memory.rel_path,
        "confidence": memory.confidence.value,
        "verification": memory.verification or "",
        "created_at": memory.created_at.isoformat(),
        "updated_at": memory.updated_at.isoformat(),
        "error_signatures_json": json.dumps(memory.error_signatures or []),
        "files_json": json.dumps(memory.files or []),
        "commands_run_json": json.dumps(memory.commands_run or []),
    }


def _memory_from_chroma(id_: str, document: str, metadata: dict[str, Any]) -> Memory:
    def _load_json_list(key: str) -> Optional[list[str]]:
        raw = metadata.get(key)
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            return None
        return None

    props: dict[str, Any] = {
        "text": document,
        "mem_type": metadata.get("mem_type", "finding"),
        "tags": [t for t in str(metadata.get("tags_csv", "")).split(",") if t],
        "scope_type": metadata.get("scope_type", "project"),
        "scope_id": metadata.get("scope_id", ""),
        "repo": metadata.get("repo", ""),
        "rel_path": metadata.get("rel_path", ""),
        "confidence": metadata.get("confidence", "med"),
        "verification": (metadata.get("verification") or None),
        "error_signatures": _load_json_list("error_signatures_json"),
        "files": _load_json_list("files_json"),
        "commands_run": _load_json_list("commands_run_json"),
    }

    created_at = metadata.get("created_at")
    if created_at:
        props["created_at"] = created_at
    updated_at = metadata.get("updated_at")
    if updated_at:
        props["updated_at"] = updated_at

    principal_type = str(metadata.get("principal_type") or "").strip()
    if principal_type:
        props["principal_type"] = principal_type

    principal_id = str(metadata.get("principal_id") or "").strip()
    if principal_id:
        props["principal_id"] = principal_id

    bot_id = str(metadata.get("bot_id") or "").strip()
    if bot_id:
        props["bot_id"] = bot_id

    return memory_from_properties(id_, props)


class ChromaCache(MemoryCache):
    def __init__(self, *, path: Path, enabled: bool) -> None:
        self._path = path
        self._enabled = enabled
        self._client = None
        self._collection = None

        if not self._enabled:
            return

        self._path.mkdir(parents=True, exist_ok=True)

        chromadb = importlib.import_module("chromadb")
        self._client = chromadb.PersistentClient(path=str(self._path))
        self._collection = self._client.get_or_create_collection(name="VibeMemMemory")

    def enabled(self) -> bool:
        return self._enabled and self._collection is not None

    def upsert(self, memory: Memory) -> None:
        if not self.enabled():
            return
        assert self._collection is not None

        self._collection.upsert(
            ids=[memory.id],
            documents=[memory.text],
            metadatas=[_memory_to_chroma_metadata(memory)],
            embeddings=[_hash_embedding(memory.text)],
        )

    def delete(self, memory_id: str) -> None:
        if not self.enabled():
            return
        assert self._collection is not None
        try:
            self._collection.delete(ids=[memory_id])
        except Exception:
            return

    def search(self, req: SearchRequest) -> list[SearchHit]:
        if not self.enabled():
            return []
        assert self._collection is not None
        collection = self._collection

        def _run_query(where: dict[str, Any]) -> list[SearchHit]:
            # Try vector query first; fall back to scan+score if Chroma's where operators differ.
            try:
                res = collection.query(
                    query_embeddings=[_hash_embedding(req.query)],
                    n_results=req.top_k,
                    where=where,
                    include=["documents", "metadatas", "distances"],
                )
                ids = (res.get("ids") or [[]])[0]
                docs = (res.get("documents") or [[]])[0]
                metas = (res.get("metadatas") or [[]])[0]
                dists = (res.get("distances") or [[]])[0]

                hits: list[SearchHit] = []
                for id_, doc, meta, dist in zip(ids, docs, metas, dists):
                    mem = _memory_from_chroma(str(id_), str(doc), dict(meta or {}))
                    score = 1.0 / (1.0 + float(dist)) if dist is not None else 0.0
                    hits.append(SearchHit(id=str(id_), score=float(score), memory=mem, source="chroma"))
                return hits
            except Exception:
                pass

            try:
                res2 = collection.get(include=["documents", "metadatas", "ids"])
            except Exception:
                return []

            ids2 = res2.get("ids") or []
            docs2 = res2.get("documents") or []
            metas2 = res2.get("metadatas") or []

            allowed_scope_type = where.get("scope_type")
            allowed_scope_ids: Optional[set[str]] = None
            if isinstance(where.get("scope_id"), dict) and "$in" in where["scope_id"]:
                allowed_scope_ids = set(str(x) for x in where["scope_id"]["$in"])

            hits2: list[SearchHit] = []
            for id_, doc, meta in zip(ids2, docs2, metas2):
                meta_d = dict(meta or {})
                if allowed_scope_type is not None and meta_d.get("scope_type") != allowed_scope_type:
                    continue
                if allowed_scope_ids is not None and str(meta_d.get("scope_id", "")) not in allowed_scope_ids:
                    continue
                mem = _memory_from_chroma(str(id_), str(doc), meta_d)
                score = simple_text_score(req.query, mem.text)
                hits2.append(SearchHit(id=str(id_), score=float(score), memory=mem, source="chroma"))
            return hits2

        where_project: dict[str, Any] = {"scope_type": req.scope_type}
        if req.scope_ids:
            where_project["scope_id"] = {"$in": list(req.scope_ids)}

        hits = _run_query(where_project)

        if req.include_global and req.scope_type != "global":
            hits.extend(_run_query({"scope_type": "global"}))

        # De-dupe + rank
        best: dict[str, SearchHit] = {}
        for h in hits:
            if h.id not in best or h.score > best[h.id].score:
                best[h.id] = h

        out = sorted(best.values(), key=lambda h: h.score, reverse=True)
        return out[: req.top_k]

    def rebuild(self, memories: Sequence[Memory]) -> None:
        if not self.enabled():
            return
        assert self._client is not None

        try:
            self._client.delete_collection(name="VibeMemMemory")
        except Exception:
            pass

        self._collection = self._client.get_or_create_collection(name="VibeMemMemory")

        for m in memories:
            self.upsert(m)

    def count(self) -> Optional[int]:
        if not self.enabled():
            return None
        assert self._collection is not None
        try:
            return int(self._collection.count())
        except Exception:
            return None
