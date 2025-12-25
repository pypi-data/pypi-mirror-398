from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal, NoReturn, Optional

import typer
from weaviate.collections.classes import filters as wfilters

from vibemem.config import (
    VibememConfig,
    load_config,
    read_config_file as read_config_file_data,
    redact_config_for_display,
    write_config_file as write_config_file_data,
)
from vibemem.models import Confidence, ListFilters, MemType, Memory, MemoryUpdate, PrincipalType, ScopeType
from vibemem.scope import ScopeInfo, derive_scope, scope_chain
from vibemem.store.base import ConfigError, ConnectionError, NotFoundError, SearchRequest
from vibemem.store.chroma_cache import ChromaCache, chroma_present_on_disk, default_chroma_path
from vibemem.store.weaviate_store import WeaviateStore
from vibemem.util import emit, normalize_where_paths, parse_csv_list, uniq


app = typer.Typer(
    name="vibemem",
    help="VibeMem: manage 'memories' for vibe-coding agents (Weaviate + optional Chroma cache).",
    add_completion=False,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

config_app = typer.Typer(
    help="Configuration commands.",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(config_app, name="config")


ScopeTypeOpt = Optional[Literal["global", "project"]]


class CacheModeOpt(str, Enum):
    auto = "auto"
    on = "on"
    off = "off"


@dataclass(frozen=True)
class Runtime:
    cfg: VibememConfig
    scope: ScopeInfo
    as_json: bool
    config_error: Optional[str] = None


def _parse_scope_type(scope_type: Optional[str]) -> ScopeTypeOpt:
    if scope_type is None:
        return None
    st = scope_type.strip().lower()
    if st not in ("global", "project"):
        raise typer.BadParameter("scope-type must be 'global' or 'project'")
    return st  # type: ignore[return-value]


def _validate_granularity(granularity: str) -> str:
    g = (granularity or "").strip().lower()
    if g in ("repo", "cwd"):
        return g
    if g.startswith("path:"):
        n = g.split(":", 1)[1]
        try:
            if int(n) <= 0:
                raise ValueError
        except ValueError:
            raise typer.BadParameter("granularity 'path:N' requires N to be a positive integer")
        return g
    raise typer.BadParameter("granularity must be 'repo', 'cwd', or 'path:N'")


def _cache_enabled(mode: CacheModeOpt, scope: ScopeInfo) -> tuple[bool, Path]:
    path = default_chroma_path(scope)
    mode_s = str(mode)
    if mode_s == "off":
        return False, path
    if mode_s == "on":
        return True, path
    # auto
    return chroma_present_on_disk(path), path


def _die(rt: Runtime, message: str, *, code: int = 1, error_type: str = "error") -> NoReturn:
    emit({"ok": False, "error": {"type": error_type, "message": message}}, as_json=rt.as_json)
    raise typer.Exit(code=code)


def _open_cache_if_enabled(rt: Runtime, mode: CacheModeOpt, scope: ScopeInfo) -> ChromaCache:
    enabled, path = _cache_enabled(mode, scope)
    try:
        return ChromaCache(path=path, enabled=enabled)
    except ModuleNotFoundError:
        if enabled:
            _die(rt, "Chroma cache requested but 'chromadb' is not installed.", code=2, error_type="missing_dependency")
        return ChromaCache(path=path, enabled=False)


def _open_store(rt: Runtime) -> WeaviateStore:
    return WeaviateStore(rt.cfg)


def _open_store_or_die(rt: Runtime) -> WeaviateStore:
    try:
        return WeaviateStore(rt.cfg)
    except ConnectionError as e:
        _die(rt, str(e), code=2, error_type="connection")
        raise


def _apply_specificity_boost(hits: list[dict], scope_ids: list[str]) -> list[dict]:
    if not scope_ids:
        return hits

    idx: dict[str, int] = {sid: i for i, sid in enumerate(scope_ids)}
    denom = max(len(scope_ids) - 1, 1)

    for h in hits:
        mem = h.get("memory", {})
        try:
            base = float(h.get("score", 0.0))
        except Exception:
            base = 0.0

        scope_type = mem.get("scope_type")
        scope_id = mem.get("scope_id")

        boost = 0.0
        if scope_type == "project" and isinstance(scope_id, str) and scope_id in idx:
            specificity = (denom - idx[scope_id]) / float(denom)
            boost = 0.05 * specificity
        elif scope_type == "global":
            boost = 0.01

        h["score"] = base + boost

    hits.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    return hits


@app.callback()
def _main(
    ctx: typer.Context,
    json_output: Annotated[bool, typer.Option("--json/--human", help="Default is --json.")] = True,
    repo_root: Annotated[Optional[Path], typer.Option("--repo-root", help="Override repo root path.")] = None,
    scope_type: Annotated[
        Optional[str], typer.Option("--scope-type", help="Override scope type: global|project.")
    ] = None,
    scope_id: Annotated[Optional[str], typer.Option("--scope-id", help="Override scope id.")] = None,
    granularity: Annotated[str, typer.Option("--granularity", help="repo|cwd|path:N")] = "repo",
) -> None:
    config_error: Optional[str] = None
    try:
        cfg = load_config()
    except Exception as e:
        # Allow `vibemem config ...` commands to run even if the config file is invalid,
        # so users can repair it via the CLI.
        if ctx.invoked_subcommand == "config":
            cfg = VibememConfig()
            config_error = str(e)
        else:
            # ctx.obj not available yet; emit minimal error
            if json_output:
                import json as _json

                print(
                    _json.dumps(
                        {"ok": False, "error": {"type": "config", "message": str(e)}}, separators=(",", ":")
                    )
                )
            else:
                raise typer.BadParameter(str(e))
            raise typer.Exit(code=2)

    scope_type_override = _parse_scope_type(scope_type)
    granularity = _validate_granularity(granularity)

    scope = derive_scope(
        Path.cwd(),
        repo_root_override=repo_root,
        scope_type_override=scope_type_override,
        scope_id_override=scope_id,
        granularity=granularity,
    )
    ctx.obj = Runtime(cfg=cfg, scope=scope, as_json=json_output, config_error=config_error)


@app.command()
def scope(ctx: typer.Context) -> None:
    rt: Runtime = ctx.obj
    enabled_auto, chroma_path = _cache_enabled(rt.cfg.cache_mode, rt.scope)
    emit(
        {
            "cwd": str(rt.scope.cwd),
            "repo_root": str(rt.scope.repo_root) if rt.scope.repo_root else None,
            "repo_slug": rt.scope.repo_slug,
            "rel_path": rt.scope.rel_path,
            "scope_type": rt.scope.scope_type,
            "scope_id": rt.scope.scope_id,
            "cache_mode": rt.cfg.cache_mode,
            "chroma_path": str(chroma_path),
            "chroma_present": chroma_present_on_disk(chroma_path),
            "chroma_enabled_auto": enabled_auto,
        },
        as_json=rt.as_json,
    )


@config_app.command("show")
def config_show(ctx: typer.Context) -> None:
    rt: Runtime = ctx.obj
    out = redact_config_for_display(rt.cfg)
    if rt.config_error:
        out["config_error"] = rt.config_error
    emit(out, as_json=rt.as_json)


@config_app.command("path")
def config_path(ctx: typer.Context) -> None:
    rt: Runtime = ctx.obj
    emit({"config_file": str(VibememConfig.config_file())}, as_json=rt.as_json)


@config_app.command("init")
def config_init(
    ctx: typer.Context,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing config file.")] = False,
) -> None:
    rt: Runtime = ctx.obj
    path = VibememConfig.config_file()
    if path.exists() and not force:
        _die(rt, f"Config file already exists: {path}", code=2, error_type="config")

    write_config_file_data(
        {
            "_comment": (
                "VibeMem config file. Values here act as defaults and can be overridden by environment "
                "variables (VIBEMEM_*). For example, VIBEMEM_PRINCIPAL_TYPE / VIBEMEM_PRINCIPAL_ID "
                "override the principal defaults below."
            ),
            "weaviate_url": None,
            "weaviate_grpc_url": None,
            "weaviate_api_key": None,
            "embedding_host": None,
            "embedding_port": None,
            "embedding_model": None,
            "weaviate_collection": "VibeMemMemory",
            "cache_mode": "auto",
            "principal_type": None,
            "principal_id": None,
            "request_timeout_s": 10.0,
        },
        path=path,
    )
    emit({"ok": True, "config_file": str(path)}, as_json=rt.as_json)


@config_app.command("set")
def config_set(
    ctx: typer.Context,
    weaviate_url: Annotated[Optional[str], typer.Option("--weaviate-url")] = None,
    weaviate_grpc_url: Annotated[Optional[str], typer.Option("--weaviate-grpc-url")] = None,
    weaviate_api_key: Annotated[Optional[str], typer.Option("--weaviate-api-key")] = None,
    clear_weaviate_api_key: Annotated[
        bool, typer.Option("--clear-weaviate-api-key", help="Remove the API key from the config file.")
    ] = False,
    embedding_host: Annotated[Optional[str], typer.Option("--embedding-host")] = None,
    embedding_port: Annotated[Optional[int], typer.Option("--embedding-port")] = None,
    embedding_model: Annotated[Optional[str], typer.Option("--embedding-model")] = None,
    weaviate_collection: Annotated[Optional[str], typer.Option("--weaviate-collection")] = None,
    cache_mode: Annotated[Optional[CacheModeOpt], typer.Option("--cache-mode", help="auto|on|off")] = None,
    principal_type: Annotated[
        Optional[PrincipalType],
        typer.Option("--principal-type", help="Default principal_type for new memories: user|bot|org|shared."),
    ] = None,
    principal_id: Annotated[
        Optional[str],
        typer.Option("--principal-id", help="Default principal_id for new memories (env overrides)."),
    ] = None,
    request_timeout_s: Annotated[Optional[float], typer.Option("--request-timeout-s")] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite even if the existing config file contains invalid JSON."),
    ] = False,
) -> None:
    rt: Runtime = ctx.obj
    path = VibememConfig.config_file()

    if (
        weaviate_url is None
        and weaviate_grpc_url is None
        and weaviate_api_key is None
        and not clear_weaviate_api_key
        and embedding_host is None
        and embedding_port is None
        and embedding_model is None
        and weaviate_collection is None
        and cache_mode is None
        and principal_type is None
        and principal_id is None
        and request_timeout_s is None
    ):
        raise typer.BadParameter("No settings provided. Pass one or more --weaviate-* / --cache-mode / --request-timeout-s.")

    try:
        current = read_config_file_data(path=path)
    except ConfigError as e:
        if not force:
            _die(rt, str(e), code=2, error_type="config")
        current = {}

    updated = dict(current)

    if weaviate_url is not None:
        updated["weaviate_url"] = weaviate_url
    if weaviate_grpc_url is not None:
        updated["weaviate_grpc_url"] = weaviate_grpc_url
    if embedding_host is not None:
        updated["embedding_host"] = embedding_host
    if embedding_port is not None:
        updated["embedding_port"] = embedding_port
    if embedding_model is not None:
        updated["embedding_model"] = embedding_model
    if weaviate_collection is not None:
        updated["weaviate_collection"] = weaviate_collection
    if cache_mode is not None:
        updated["cache_mode"] = cache_mode.value
    if principal_type is not None:
        updated["principal_type"] = principal_type.value
    if principal_id is not None:
        updated["principal_id"] = principal_id
    if request_timeout_s is not None:
        updated["request_timeout_s"] = request_timeout_s

    if clear_weaviate_api_key:
        updated.pop("weaviate_api_key", None)
    elif weaviate_api_key is not None:
        updated["weaviate_api_key"] = weaviate_api_key

    # Validate before writing. Keep the raw dict (so secrets stay as strings on disk).
    try:
        VibememConfig.model_validate(updated)
    except Exception as e:
        _die(rt, f"Invalid config: {e}", code=2, error_type="config")

    write_config_file_data(updated, path=path)

    # Show effective config (env vars override file values).
    emit({"ok": True, **redact_config_for_display(load_config())}, as_json=rt.as_json)


@config_app.command("unset")
def config_unset(
    ctx: typer.Context,
    keys: Annotated[list[str], typer.Argument(help="One or more config keys to remove.")],
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite even if the existing config file contains invalid JSON."),
    ] = False,
) -> None:
    rt: Runtime = ctx.obj
    path = VibememConfig.config_file()

    if not keys:
        raise typer.BadParameter("Provide one or more keys to unset.")

    try:
        current = read_config_file_data(path=path)
    except ConfigError as e:
        if not force:
            _die(rt, str(e), code=2, error_type="config")
        current = {}

    updated = dict(current)
    for k in keys:
        updated.pop(k, None)

    try:
        VibememConfig.model_validate(updated)
    except Exception as e:
        _die(rt, f"Invalid config: {e}", code=2, error_type="config")

    write_config_file_data(updated, path=path)
    emit({"ok": True, **redact_config_for_display(load_config())}, as_json=rt.as_json)


@app.command()
def search(
    ctx: typer.Context,
    query: Annotated[str, typer.Argument(help="Search query text.")],
    top: Annotated[int, typer.Option("--top", help="Max results.")] = 8,
    include_global: Annotated[bool, typer.Option("--include-global/--no-include-global")] = True,
    include_parents: Annotated[bool, typer.Option("--include-parents/--no-include-parents")] = True,
    cache: Annotated[CacheModeOpt, typer.Option("--cache", help="auto|on|off")] = CacheModeOpt.auto,
) -> None:
    rt: Runtime = ctx.obj

    scope_ids: list[str] = []
    if rt.scope.scope_type == "project":
        scope_ids = scope_chain(rt.scope, include_parents=include_parents)
    else:
        include_global = False

    cache_mode = CacheModeOpt(rt.cfg.cache_mode) if cache == CacheModeOpt.auto else cache
    chroma = _open_cache_if_enabled(rt, cache_mode, rt.scope)

    req = SearchRequest(
        query=query,
        scope_type=rt.scope.scope_type,
        scope_ids=scope_ids,
        include_global=include_global,
        top_k=top,
    )

    hits: list[dict] = []
    used: str = "weaviate"

    try:
        store = _open_store(rt)
        try:
            whits = store.search(req)
        finally:
            store.close()

        hits = [h.model_dump(mode="json") for h in whits]
    except ConnectionError as e:
        if chroma.enabled():
            used = "chroma"
            chits = chroma.search(req)
            hits = [h.model_dump(mode="json") for h in chits]
        else:
            _die(rt, str(e), code=2, error_type="connection")

    hits = _apply_specificity_boost(hits, scope_ids)
    deduped: list[dict] = []
    seen: set[str] = set()
    for h in hits:
        hid = str(h.get("id", ""))
        if not hid or hid in seen:
            continue
        seen.add(hid)
        deduped.append(h)

    emit(
        {
            "query": query,
            "scope_type": rt.scope.scope_type,
            "scope_ids": scope_ids,
            "include_global": include_global,
            "include_parents": include_parents,
            "used": used,
            "hits": deduped[:top],
        },
        as_json=rt.as_json,
    )


@app.command()
def add(
    ctx: typer.Context,
    mem_type: Annotated[MemType, typer.Option("--type", help="core|finding|recipe|gotcha|preference")],
    text: Annotated[str, typer.Option("--text", help="Memory content.")],
    tags: Annotated[Optional[str], typer.Option("--tags", help="Comma-separated tags.")] = None,
    principal_type: Annotated[
        Optional[PrincipalType], typer.Option("--principal-type", help="user|bot|org|shared")
    ] = None,
    principal_id: Annotated[
        Optional[str], typer.Option("--principal-id", help="Memory owner id (default: $VIBEMEM_PRINCIPAL_ID or OS user).")
    ] = None,
    bot_id: Annotated[Optional[str], typer.Option("--bot-id", help="Restrict to a specific bot.")] = None,
    confidence: Annotated[Confidence, typer.Option("--confidence")] = Confidence.med,
    verification: Annotated[Optional[str], typer.Option("--verification")] = None,
    errors: Annotated[list[str], typer.Option("--error", help="Repeatable error signature.")] = [],
    files: Annotated[list[str], typer.Option("--file", help="Repeatable file path.")] = [],
    cmds: Annotated[list[str], typer.Option("--cmd", help="Repeatable command run.")] = [],
    cache: Annotated[CacheModeOpt, typer.Option("--cache", help="auto|on|off")] = CacheModeOpt.auto,
) -> None:
    rt: Runtime = ctx.obj
    cache_mode = CacheModeOpt(rt.cfg.cache_mode) if cache == CacheModeOpt.auto else cache
    chroma = _open_cache_if_enabled(rt, cache_mode, rt.scope)

    extra: dict[str, object] = {}
    if principal_type is not None:
        extra["principal_type"] = principal_type
    elif rt.cfg.principal_type is not None:
        extra["principal_type"] = rt.cfg.principal_type
    if principal_id is not None:
        extra["principal_id"] = principal_id
    elif rt.cfg.principal_id is not None:
        extra["principal_id"] = rt.cfg.principal_id
    if bot_id is not None:
        extra["bot_id"] = bot_id

    m = Memory(
        text=text,
        mem_type=mem_type,
        tags=uniq(parse_csv_list(tags)),
        scope_type=ScopeType(rt.scope.scope_type),
        scope_id=rt.scope.scope_id,
        repo=rt.scope.repo_slug,
        rel_path=rt.scope.rel_path,
        confidence=confidence,
        verification=verification,
        error_signatures=errors or None,
        files=normalize_where_paths(files) or None,
        commands_run=cmds or None,
        **extra,
    )

    try:
        store = _open_store_or_die(rt)
        try:
            created = store.add(m)
        finally:
            store.close()
    except ConnectionError as e:
        _die(rt, str(e), code=2, error_type="connection")

    if chroma.enabled():
        chroma.upsert(created)

    emit(created, as_json=rt.as_json)


@app.command()
def edit(
    ctx: typer.Context,
    memory_id: Annotated[str, typer.Argument(help="Memory UUID.")],
    text: Annotated[Optional[str], typer.Option("--text")] = None,
    mem_type: Annotated[
        Optional[MemType], typer.Option("--type", help="core|finding|recipe|gotcha|preference")
    ] = None,
    tags: Annotated[Optional[str], typer.Option("--tags")] = None,
    principal_type: Annotated[Optional[PrincipalType], typer.Option("--principal-type", help="user|bot|org|shared")] = None,
    principal_id: Annotated[Optional[str], typer.Option("--principal-id", help="Memory owner id.")] = None,
    bot_id: Annotated[Optional[str], typer.Option("--bot-id", help="Restrict to a specific bot.")] = None,
    confidence: Annotated[Optional[Confidence], typer.Option("--confidence")] = None,
    verification: Annotated[Optional[str], typer.Option("--verification")] = None,
    cache: Annotated[CacheModeOpt, typer.Option("--cache", help="auto|on|off")] = CacheModeOpt.auto,
) -> None:
    rt: Runtime = ctx.obj
    cache_mode = CacheModeOpt(rt.cfg.cache_mode) if cache == CacheModeOpt.auto else cache
    chroma = _open_cache_if_enabled(rt, cache_mode, rt.scope)

    upd = MemoryUpdate(
        text=text,
        mem_type=mem_type,
        tags=uniq(parse_csv_list(tags)) if tags is not None else None,
        principal_type=principal_type,
        principal_id=principal_id,
        bot_id=bot_id,
        confidence=confidence,
        verification=verification,
    )

    try:
        store = _open_store_or_die(rt)
        try:
            updated = store.edit(memory_id, upd)
        finally:
            store.close()
    except NotFoundError as e:
        _die(rt, str(e), code=3, error_type="not_found")
    except ConnectionError as e:
        _die(rt, str(e), code=2, error_type="connection")

    if chroma.enabled():
        chroma.upsert(updated)

    emit(updated, as_json=rt.as_json)


@app.command("rm")
def rm_cmd(
    ctx: typer.Context,
    memory_id: Annotated[str, typer.Argument(help="Memory UUID.")],
    cache: Annotated[CacheModeOpt, typer.Option("--cache", help="auto|on|off")] = CacheModeOpt.auto,
) -> None:
    rt: Runtime = ctx.obj
    cache_mode = CacheModeOpt(rt.cfg.cache_mode) if cache == CacheModeOpt.auto else cache
    chroma = _open_cache_if_enabled(rt, cache_mode, rt.scope)

    try:
        store = _open_store_or_die(rt)
        try:
            store.delete(memory_id)
        finally:
            store.close()
    except NotFoundError as e:
        _die(rt, str(e), code=3, error_type="not_found")
    except ConnectionError as e:
        _die(rt, str(e), code=2, error_type="connection")

    if chroma.enabled():
        chroma.delete(memory_id)

    emit({"deleted": memory_id}, as_json=rt.as_json)


@app.command("list")
def list_cmd(
    ctx: typer.Context,
    scope: Annotated[str, typer.Option("--scope", help="global|project|all")] = "project",
    mem_type: Annotated[Optional[MemType], typer.Option("--type")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag")] = None,
    limit: Annotated[int, typer.Option("--limit")] = 20,
) -> None:
    rt: Runtime = ctx.obj
    scope = scope.strip().lower()
    if scope not in ("global", "project", "all"):
        raise typer.BadParameter("scope must be global|project|all")

    repo_filter: Optional[str] = None
    if scope == "project" and rt.scope.repo_slug:
        repo_filter = rt.scope.repo_slug

    filters = ListFilters(scope=scope, mem_type=mem_type, tag=tag, limit=limit, repo=repo_filter, scope_ids=None)

    try:
        store = _open_store_or_die(rt)
        try:
            memories = store.list(filters)
        finally:
            store.close()
    except ConnectionError as e:
        _die(rt, str(e), code=2, error_type="connection")

    emit(
        {"scope": scope, "repo": repo_filter, "count": len(memories), "memories": [m.model_dump(mode="json") for m in memories]},
        as_json=rt.as_json,
    )


@app.command()
def sync(
    ctx: typer.Context,
    pull: Annotated[bool, typer.Option("--pull", help="Pull from Weaviate into local Chroma cache.")] = False,
    limit: Annotated[int, typer.Option("--limit")] = 200,
) -> None:
    rt: Runtime = ctx.obj
    if not pull:
        emit({"todo": "push/offline queue not implemented yet", "hint": "use --pull"}, as_json=rt.as_json)
        raise typer.Exit(code=2)

    if rt.scope.scope_type != "project":
        raise typer.BadParameter("sync --pull requires project scope (run inside a repo or set --scope-type project).")

    chroma = _open_cache_if_enabled(rt, "on", rt.scope)
    if not chroma.enabled():
        raise typer.Exit(code=2)

    scope_ids = scope_chain(rt.scope, include_parents=True)

    try:
        store = _open_store_or_die(rt)
        try:
            memories = store.list(
                ListFilters(
                    scope="project",
                    mem_type=None,
                    tag=None,
                    limit=limit,
                    repo=rt.scope.repo_slug,
                    scope_ids=scope_ids,
                )
            )
        finally:
            store.close()
    except ConnectionError as e:
        _die(rt, str(e), code=2, error_type="connection")

    chroma.rebuild(memories)

    emit(
        {
            "pulled": len(memories),
            "scope_ids": scope_ids,
            "chroma_path": str(default_chroma_path(rt.scope)),
            "chroma_count": chroma.count(),
        },
        as_json=rt.as_json,
    )


@app.command()
def reembed(
    ctx: typer.Context,
    scope: Annotated[str, typer.Option("--scope", help="global|project|all")] = "project",
    repo: Annotated[Optional[str], typer.Option("--repo", help="Repo slug filter (default: current repo).")] = None,
    limit: Annotated[int, typer.Option("--limit", help="Max objects to process (0 = unlimited).")] = 0,
    batch_size: Annotated[int, typer.Option("--batch-size", help="Embedding batch size.")] = 32,
    all_records: Annotated[bool, typer.Option("--all", help="Re-embed all matching records (default: only missing vectors).")] = False,
    to_collection: Annotated[
        Optional[str],
        typer.Option(
            "--to-collection",
            help="Write re-embedded copies into a new Weaviate collection (leaves the current collection untouched).",
        ),
    ] = None,
) -> None:
    rt: Runtime = ctx.obj
    scope = scope.strip().lower()
    if scope not in ("global", "project", "all"):
        raise typer.BadParameter("scope must be global|project|all")
    if limit < 0:
        raise typer.BadParameter("limit must be >= 0")
    if batch_size <= 0 or batch_size > 512:
        raise typer.BadParameter("batch-size must be in 1..512")

    # Default repo filter matches `list --scope project` behavior.
    repo_filter = repo
    if repo_filter is None and scope == "project" and rt.scope.repo_slug:
        repo_filter = rt.scope.repo_slug

    if not rt.cfg.embedding_host or not rt.cfg.embedding_port:
        _die(
            rt,
            "Embedding is not configured. Set VIBEMEM_EMBEDDING_HOST and VIBEMEM_EMBEDDING_PORT (and optionally VIBEMEM_EMBEDDING_MODEL).",
            code=2,
            error_type="config",
        )

    src = _open_store_or_die(rt)
    dst = src
    if to_collection:
        dst_cfg = rt.cfg.model_copy(update={"weaviate_collection": to_collection})
        dst = WeaviateStore(dst_cfg)

    try:
        embedder = getattr(dst, "_embedder", None)
        if not embedder:
            _die(rt, "Embedding client is not available (check embedding_host/port config).", code=2, error_type="config")

        # Compute the new embedding dimension once to detect obvious mismatches for in-place updates.
        try:
            probe = embedder.embed(["probe"])
            new_dim = len(probe[0]) if probe and probe[0] is not None else 0
        except Exception as e:
            _die(rt, f"Embedding probe failed: {e}", code=2, error_type="embedding")

        filt = None
        if scope in ("global", "project"):
            filt = wfilters.Filter.by_property("scope_type").equal(scope)

        if repo_filter:
            f_repo = wfilters.Filter.by_property("repo").equal(repo_filter)
            filt = f_repo if filt is None else wfilters.Filter.all_of([filt, f_repo])

        existing_dim: Optional[int] = None
        if not to_collection:
            try:
                qr0 = src._collection.query.fetch_objects(limit=25, filters=filt, include_vector=True, return_properties=False)
                for obj in getattr(qr0, "objects", []) or []:
                    vec = getattr(obj, "vector", None)
                    if isinstance(vec, list) and vec:
                        existing_dim = len(vec)
                        break
            except Exception:
                existing_dim = None

            if existing_dim is not None and new_dim and existing_dim != new_dim:
                _die(
                    rt,
                    f"Embedding dimension mismatch: existing vectors appear to be dim={existing_dim} but the current embedding model returns dim={new_dim}. "
                    "Use --to-collection to migrate to a fresh collection, or switch back to the previous embedding model.",
                    code=2,
                    error_type="embedding",
                )

        page_size = max(batch_size, 64)
        after = None
        scanned = 0
        selected = 0
        updated = 0
        inserted = 0
        skipped_no_text = 0
        skipped_has_vector = 0
        errors = 0

        while True:
            if limit and scanned >= limit:
                break

            fetch_limit = page_size
            if limit:
                fetch_limit = min(fetch_limit, limit - scanned)

            qr = src._collection.query.fetch_objects(
                limit=fetch_limit,
                after=after,
                filters=filt,
                include_vector=(not all_records and not to_collection),
                return_properties=True if to_collection else ["text"],
            )
            objs = getattr(qr, "objects", []) or []
            if not objs:
                break

            after = getattr(objs[-1], "uuid", None)
            scanned += len(objs)

            batch_ids: list[str] = []
            batch_texts: list[str] = []
            batch_props: list[dict] = []

            for obj in objs:
                uid = getattr(obj, "uuid", None)
                if uid is None:
                    continue

                props = dict(getattr(obj, "properties", {}) or {})
                text = props.get("text")
                if not isinstance(text, str) or not text.strip():
                    skipped_no_text += 1
                    continue

                if not all_records and not to_collection:
                    vec = getattr(obj, "vector", None)
                    if isinstance(vec, list) and vec:
                        skipped_has_vector += 1
                        continue

                batch_ids.append(str(uid))
                batch_texts.append(text)
                if to_collection:
                    batch_props.append(props)

            if not batch_texts:
                continue

            selected += len(batch_texts)
            try:
                vectors = embedder.embed(batch_texts)
            except Exception as e:
                _die(rt, f"Embedding batch failed: {e}", code=2, error_type="embedding")

            for i, (mid, vec) in enumerate(zip(batch_ids, vectors)):
                try:
                    if to_collection:
                        props = batch_props[i]
                        # Best-effort: Weaviate rejects unknown properties on insert; drop nulls too.
                        clean = {k: v for k, v in props.items() if v is not None}
                        try:
                            dst._collection.data.insert(properties=clean, uuid=mid, vector=vec)
                            inserted += 1
                        except Exception:
                            dst._collection.data.replace(uuid=mid, properties=clean, vector=vec)
                            inserted += 1
                    else:
                        src._collection.data.update(uuid=mid, vector=vec)
                        updated += 1
                except Exception:
                    errors += 1

        emit(
            {
                "ok": errors == 0,
                "mode": "migrate" if to_collection else "in_place",
                "source_collection": rt.cfg.weaviate_collection,
                "dest_collection": to_collection or rt.cfg.weaviate_collection,
                "scope": scope,
                "repo": repo_filter,
                "scanned": scanned,
                "selected": selected,
                "updated": updated,
                "inserted": inserted,
                "skipped_no_text": skipped_no_text,
                "skipped_has_vector": skipped_has_vector,
                "embedding_dim": new_dim or None,
                "existing_vector_dim": existing_dim,
                "errors": errors,
            },
            as_json=rt.as_json,
        )
    finally:
        try:
            src.close()
        except Exception:
            pass
        if dst is not src:
            try:
                dst.close()
            except Exception:
                pass


# Typer/Click errors (BadParameter, etc.) are handled by Typer itself.
# For domain errors we emit JSON and exit non-zero inside command handlers.


if __name__ == "__main__":
    app()
