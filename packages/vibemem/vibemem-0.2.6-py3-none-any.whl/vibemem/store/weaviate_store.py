from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import weaviate
from weaviate.auth import AuthApiKey
from weaviate.classes.config import Configure, DataType, Property
from weaviate.collections.classes import filters as wfilters
from weaviate.collections.classes import grpc

from vibemem.config import VibememConfig
from vibemem.embeddings import EmbeddingClient, EmbeddingError
from vibemem.models import (
    _now_iso,
    ListFilters,
    Memory,
    MemoryUpdate,
    SearchHit,
    memory_from_properties,
    memory_to_weaviate_properties,
)
from vibemem.store.base import ConnectionError, NotFoundError, SearchRequest


@dataclass(frozen=True)
class _ParsedEndpoint:
    host: str
    port: int
    secure: bool


def _parse_host_port(url: str, *, default_port_http: int, default_port_https: int) -> _ParsedEndpoint:
    from urllib.parse import urlparse

    url = url.strip()
    # Accept host:port inputs by assuming http://
    if "://" not in url:
        url = "http://" + url

    parsed = urlparse(url)
    scheme = parsed.scheme.lower() if parsed.scheme else "http"
    secure = scheme == "https"

    host = parsed.hostname or ""
    if not host:
        raise ValueError(f"Invalid URL (missing host): {url}")

    if parsed.port is not None:
        port = int(parsed.port)
    else:
        port = default_port_https if secure else default_port_http

    return _ParsedEndpoint(host=host, port=port, secure=secure)


def _looks_like_cloud_url(url: str) -> bool:
    try:
        from urllib.parse import urlparse

        url = url.strip()
        if "://" not in url:
            url = "https://" + url
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host.endswith(".weaviate.cloud") or host.endswith(".weaviate.network") or host.endswith(".wcs.api.weaviate.io")


def _missing_vectorizer_error(err: Exception) -> bool:
    msg = str(err)
    return "VectorFromInput" in msg and "without vectorizer" in msg


class WeaviateStore:
    def __init__(self, cfg: VibememConfig) -> None:
        self._cfg = cfg
        self._collection_name = cfg.weaviate_collection
        self._embedder: Optional[EmbeddingClient] = None

        if not cfg.weaviate_url:
            raise ConnectionError("Weaviate URL is not configured (set VIBEMEM_WEAVIATE_URL).")

        if cfg.embedding_host and cfg.embedding_port:
            self._embedder = EmbeddingClient(
                host=cfg.embedding_host,
                port=int(cfg.embedding_port),
                model=cfg.embedding_model,
                timeout_s=cfg.request_timeout_s,
            )

        timeout = weaviate.config.Timeout(
            query=cfg.request_timeout_s,
            insert=max(cfg.request_timeout_s, 20.0),
            init=min(cfg.request_timeout_s, 10.0),
        )
        additional_config = weaviate.config.AdditionalConfig(timeout=timeout, trust_env=True)

        auth_credentials = None
        if cfg.weaviate_api_key:
            auth_credentials = AuthApiKey(api_key=cfg.weaviate_api_key.get_secret_value())

        try:
            if _looks_like_cloud_url(cfg.weaviate_url):
                if not auth_credentials:
                    raise ConnectionError("Weaviate Cloud URL provided but API key is missing (VIBEMEM_WEAVIATE_API_KEY).")
                self._client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=cfg.weaviate_url,
                    auth_credentials=auth_credentials,
                    additional_config=additional_config,
                    skip_init_checks=False,
                )
            else:
                http = _parse_host_port(cfg.weaviate_url, default_port_http=8080, default_port_https=443)
                if cfg.weaviate_grpc_url:
                    grpc_ep = _parse_host_port(cfg.weaviate_grpc_url, default_port_http=50051, default_port_https=443)
                else:
                    grpc_ep = _ParsedEndpoint(host=http.host, port=50051, secure=http.secure)

                self._client = weaviate.connect_to_custom(
                    http_host=http.host,
                    http_port=http.port,
                    http_secure=http.secure,
                    grpc_host=grpc_ep.host,
                    grpc_port=grpc_ep.port,
                    grpc_secure=grpc_ep.secure,
                    auth_credentials=auth_credentials,
                    additional_config=additional_config,
                    skip_init_checks=False,
                )

            self._ensure_collection()
            self._collection = self._client.collections.use(self._collection_name)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Weaviate: {e}") from e

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            return

    def _ensure_collection(self) -> None:
        properties = [
            Property(name="text", data_type=DataType.TEXT),
            Property(name="mem_type", data_type=DataType.TEXT),
            Property(name="tags", data_type=DataType.TEXT_ARRAY),
            Property(name="principal_type", data_type=DataType.TEXT),
            Property(name="principal_id", data_type=DataType.TEXT),
            Property(name="bot_id", data_type=DataType.TEXT),
            Property(name="scope_type", data_type=DataType.TEXT),
            Property(name="scope_id", data_type=DataType.TEXT),
            Property(name="repo", data_type=DataType.TEXT),
            Property(name="rel_path", data_type=DataType.TEXT),
            Property(name="confidence", data_type=DataType.TEXT),
            Property(name="verification", data_type=DataType.TEXT),
            Property(name="created_at", data_type=DataType.TEXT),
            Property(name="updated_at", data_type=DataType.TEXT),
            Property(name="error_signatures", data_type=DataType.TEXT_ARRAY),
            Property(name="files", data_type=DataType.TEXT_ARRAY),
            Property(name="commands_run", data_type=DataType.TEXT_ARRAY),
        ]

        try:
            exists = self._client.collections.exists(self._collection_name)
        except Exception as e:
            raise ConnectionError(f"Cannot check Weaviate schema: {e}") from e

        if exists:
            # Best-effort schema evolution: add any missing properties.
            try:
                col = self._client.collections.use(self._collection_name)
                cfg = col.config.get(simple=True).to_dict()
                existing = {p.get("name") for p in (cfg.get("properties") or []) if isinstance(p, dict)}
                for prop in properties:
                    if prop.name in existing:
                        continue
                    try:
                        col.config.add_property(prop)
                    except Exception:
                        continue
            except Exception:
                return
            return

        # Prefer vectorizing text if module exists; fall back to no vectorizer if it doesn't.
        last_err: Optional[Exception] = None
        vectorizers = (
            (Configure.Vectorizer.none(),)
            if self._embedder
            else (Configure.Vectorizer.text2vec_transformers(), Configure.Vectorizer.none())
        )
        for vectorizer in vectorizers:
            try:
                self._client.collections.create(
                    name=self._collection_name,
                    properties=properties,
                    vectorizer_config=vectorizer,
                )
                return
            except Exception as e:
                last_err = e

        raise ConnectionError(f"Failed to create collection '{self._collection_name}': {last_err}")

    def _embed_text(self, text: str) -> Optional[list[float]]:
        embedder = getattr(self, "_embedder", None)
        if not embedder:
            return None
        try:
            vecs = embedder.embed([text])
            return vecs[0] if vecs else None
        except EmbeddingError:
            return None
        except Exception:
            return None

    def add(self, memory: Memory) -> Memory:
        props = memory_to_weaviate_properties(memory)
        vector = self._embed_text(memory.text)
        try:
            self._collection.data.insert(properties=props, uuid=memory.id, vector=vector)
        except Exception as e:
            raise ConnectionError(f"Failed to insert memory into Weaviate: {e}") from e
        return memory

    def get(self, memory_id: str) -> Memory:
        try:
            res = self._collection.query.fetch_object_by_id(
                uuid=memory_id,
                return_properties=True,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to fetch memory from Weaviate: {e}") from e

        obj = getattr(res, "object", None) or res
        if not obj:
            raise NotFoundError(f"Memory not found: {memory_id}")

        props = getattr(obj, "properties", None)
        uuid = getattr(obj, "uuid", None) or getattr(obj, "id", None) or memory_id
        if props is None:
            raise NotFoundError(f"Memory not found: {memory_id}")

        return memory_from_properties(str(uuid), dict(props))

    def edit(self, memory_id: str, update: MemoryUpdate) -> Memory:
        current = self.get(memory_id)
        patch = update.model_dump(exclude_none=True)

        merged = current.model_copy(update=patch)
        merged.updated_at = _now_iso()

        props = memory_to_weaviate_properties(merged)
        vector = self._embed_text(merged.text)
        try:
            self._collection.data.replace(uuid=memory_id, properties=props, vector=vector)
        except Exception as e:
            raise ConnectionError(f"Failed to update memory in Weaviate: {e}") from e
        return merged

    def delete(self, memory_id: str) -> None:
        try:
            ok = self._collection.data.delete_by_id(uuid=memory_id)
        except Exception as e:
            raise ConnectionError(f"Failed to delete memory in Weaviate: {e}") from e
        if ok is False:
            raise NotFoundError(f"Memory not found: {memory_id}")

    def search(self, req: SearchRequest) -> list[SearchHit]:
        # scope_type filter
        filt = wfilters.Filter.by_property("scope_type").equal(req.scope_type)

        # scope_ids OR filter
        if req.scope_ids:
            scope_filters = [wfilters.Filter.by_property("scope_id").equal(s) for s in req.scope_ids]
            filt = wfilters.Filter.all_of([filt, wfilters.Filter.any_of(scope_filters)])

        if req.include_global and req.scope_type != "global":
            global_filt = wfilters.Filter.by_property("scope_type").equal("global")
            filt = wfilters.Filter.any_of([filt, global_filt])

        query_vector = self._embed_text(req.query)

        try:
            qr = None
            if query_vector is not None:
                try:
                    qr = self._collection.query.hybrid(
                        req.query,
                        vector=query_vector,
                        query_properties=["text"],
                        limit=req.top_k,
                        filters=filt,
                        return_metadata=grpc.MetadataQuery(score=True, distance=True),
                        return_properties=True,
                    )
                except Exception:
                    qr = None

            if qr is None:
                try:
                    qr = self._collection.query.hybrid(
                        req.query,
                        query_properties=["text"],
                        limit=req.top_k,
                        filters=filt,
                        return_metadata=grpc.MetadataQuery(score=True, distance=True),
                        return_properties=True,
                    )
                except Exception as e:
                    if not _missing_vectorizer_error(e):
                        raise
                    qr = self._collection.query.bm25(
                        req.query,
                        query_properties=["text"],
                        limit=req.top_k,
                        filters=filt,
                        return_metadata=grpc.MetadataQuery(score=True),
                        return_properties=True,
                    )
        except Exception as e:
            raise ConnectionError(f"Search failed in Weaviate: {e}") from e

        hits: list[SearchHit] = []
        for obj in getattr(qr, "objects", []) or []:
            uuid = str(getattr(obj, "uuid", ""))
            props = dict(getattr(obj, "properties", {}) or {})
            mem = memory_from_properties(uuid, props)

            md = getattr(obj, "metadata", None)
            score = None
            if md is not None:
                score = getattr(md, "score", None)
                if score is None:
                    dist = getattr(md, "distance", None)
                    if dist is not None:
                        try:
                            score = 1.0 / (1.0 + float(dist))
                        except Exception:
                            score = None
            if score is None:
                score = 0.0

            hits.append(SearchHit(id=uuid, score=float(score), memory=mem, source="weaviate"))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits

    def list(self, filters: ListFilters) -> list[Memory]:
        filt: Optional[wfilters._Filters] = None

        if filters.scope in ("global", "project"):
            filt = wfilters.Filter.by_property("scope_type").equal(filters.scope)

        if filters.repo:
            f_repo = wfilters.Filter.by_property("repo").equal(filters.repo)
            filt = f_repo if filt is None else wfilters.Filter.all_of([filt, f_repo])

        if filters.scope_ids:
            f_scope = wfilters.Filter.any_of([wfilters.Filter.by_property("scope_id").equal(s) for s in filters.scope_ids])
            filt = f_scope if filt is None else wfilters.Filter.all_of([filt, f_scope])

        if filters.mem_type:
            f2 = wfilters.Filter.by_property("mem_type").equal(filters.mem_type.value)
            filt = f2 if filt is None else wfilters.Filter.all_of([filt, f2])

        if filters.tag:
            f3 = wfilters.Filter.by_property("tags").contains_any([filters.tag])
            filt = f3 if filt is None else wfilters.Filter.all_of([filt, f3])

        try:
            qr = self._collection.query.fetch_objects(
                limit=filters.limit,
                filters=filt,
                sort=grpc.Sort.by_update_time(ascending=False),
                return_properties=True,
                return_metadata=grpc.MetadataQuery(creation_time=True, last_update_time=True),
            )
        except Exception as e:
            raise ConnectionError(f"List failed in Weaviate: {e}") from e

        out: list[Memory] = []
        for obj in getattr(qr, "objects", []) or []:
            uuid = str(getattr(obj, "uuid", ""))
            props = dict(getattr(obj, "properties", {}) or {})
            out.append(memory_from_properties(uuid, props))
        return out
