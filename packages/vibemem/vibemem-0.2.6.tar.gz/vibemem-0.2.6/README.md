# VibeMem (`vibemem`)

VibeMem is a pip-installable CLI tool to manage reusable “memories” (core rules / findings / recipes / gotchas / preferences) for vibe-coding agents.

- Canonical storage: Weaviate (single collection: `VibeMemMemory`)
- Optional local cache: Chroma persisted under `~/.vibemem/chroma/` (per-repo subdirectory)
- Works from **any directory**: derives repo root + scope from your current working directory (override via flags)
- Default output: JSON (agent-friendly). Use `--human` for pretty output.

## Install

From PyPI:

```bash
python -m pip install -U vibemem
```

Editable install from this repo:

```bash
python -m pip install -e .
```

Optional cache support (Chroma):

```bash
python -m pip install -e ".[cache]"
```

Dev tools/tests:

```bash
python -m pip install -e ".[dev]"
pytest
```

### Install troubleshooting

If `pip install -U vibemem` fails with an `OSError: [Errno 2] No such file or directory`, it usually means `pip` fell back to building a dependency from source and a build tool is missing on your machine.

Try:

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -U vibemem -v
```

If it still fails, paste the full `-v` output (it should include the missing executable/file), and try a clean reinstall:

```bash
python -m pip uninstall -y vibemem
python -m pip install -U --no-cache-dir vibemem
```

## Configuration

VibeMem reads connection settings from environment variables first, then falls back to a JSON config file at `~/.vibemem/config`.

### Config file (optional)

Show where the config file lives:

```bash
vibemem config path
```

Create an empty config file:

```bash
vibemem config init
```

Set values via the CLI (writes to `~/.vibemem/config`):

```bash
vibemem config set --weaviate-url http://localhost:8080 --weaviate-grpc-url http://localhost:50051
```

You can also set defaults for new memories’ ownership fields (env vars override config):

```bash
vibemem config set --principal-type user --principal-id "alice"
```

Optional: configure a hosted embedding service so VibeMem can store vectors (for semantic/hybrid search) even when the Weaviate collection has `vectorizer = none`:

```bash
vibemem config set --embedding-host 127.0.0.1 --embedding-port 7071 --embedding-model "your-model-id"
```

The embedding service must expose either an OpenAI-compatible `POST /v1/embeddings` endpoint, or a TEI-compatible `POST /embed` endpoint.

Note: environment variables (below) override values in the config file.

### Env vars

- `VIBEMEM_WEAVIATE_URL` (required for Weaviate operations)
  - Examples: `http://localhost:8080` or `https://YOUR_CLUSTER.weaviate.cloud`
- `VIBEMEM_WEAVIATE_API_KEY` (optional; required for Weaviate Cloud URLs)
- `VIBEMEM_WEAVIATE_GRPC_URL` (optional)
  - Example: `http://localhost:50051`
- `VIBEMEM_EMBEDDING_HOST` (optional; enables client-side embeddings)
- `VIBEMEM_EMBEDDING_PORT` (optional; enables client-side embeddings)
- `VIBEMEM_EMBEDDING_MODEL` (optional; used for OpenAI-compatible `/v1/embeddings`)
- `VIBEMEM_WEAVIATE_COLLECTION` (default: `VibeMemMemory`)
- `VIBEMEM_CACHE_MODE` (default: `auto`) — `auto|on|off`
- `VIBEMEM_PRINCIPAL_TYPE` (optional) — default `principal_type` on new memories when not provided.
- `VIBEMEM_PRINCIPAL_ID` (optional; default: OS username) — default `principal_id` to store on new memories when not provided.

### Show effective config

```bash
vibemem config show
```

## Scope model

VibeMem derives scope from your current directory:

- Repo root is detected by searching upwards for `.git/` first; fallback markers: `pyproject.toml`, `package.json`, `go.mod`
- `repo_slug = basename(repo_root)`
- `rel_path = path from repo_root to cwd` (empty at repo root)

Scope ID derivation is controlled by `--granularity`:

- `repo` (default): `scope_id = repo_slug`
- `cwd`: `scope_id = repo_slug::<rel_path>`
- `path:N`: `scope_id = repo_slug::<first N path parts>`

Show current derived scope:

```bash
vibemem scope
```

## Commands

### Search

Search returns ranked memories with scope-aware bubbling (current scope → parent scopes → repo-level; and optionally global).

```bash
vibemem search "TypeError: ..." --top 8
```

Options:

- `--include-global/--no-include-global`
- `--include-parents/--no-include-parents`
- `--cache auto|on|off`

When Weaviate is unreachable and cache is ON (and built), `search` will fall back to Chroma.

### Add a memory

```bash
vibemem add --type recipe --text "Use X to fix Y" --tags "python,typing" --confidence high --verification "ran pytest"
```

Optional ownership fields (stored on the memory record):

- `--principal-type user|bot|org|shared`
- `--principal-id "..."` (defaults to `$VIBEMEM_PRINCIPAL_ID` or your OS username)
- `--bot-id "..."` (omit for “all bots”)

Add structured metadata:

```bash
vibemem add --type gotcha --text "Chroma where filters differ by version" --error "ModuleNotFoundError: chromadb" --file "vibemem/store/chroma_cache.py" --cmd "pip install -e '.[cache]'"
```

### Memory fields (schema)

This is the full set of fields on a memory record (as returned by the CLI JSON output and the Python `Memory` model):

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | `str` (UUID) | yes | Stable identifier for the memory. |
| `text` | `str` | yes | Main memory content (non-empty). |
| `mem_type` | `core\|finding\|recipe\|gotcha\|preference` | yes | Memory category. |
| `tags` | `list[str]` | yes | Tags (deduped/trimmed). |
| `principal_type` | `user\|bot\|org\|shared` | yes | Who the memory belongs to. |
| `principal_id` | `str` | yes | Owner identifier (user/bot/org id). |
| `bot_id` | `str \| null` | no | Optional bot restriction (null = applies to all bots). |
| `scope_type` | `project\|global` | yes | Which knowledge base the memory belongs to. |
| `scope_id` | `str` | yes | Scope identifier (`repo_slug` or `repo_slug::path/from/repo/root`, or `"global"`). |
| `repo` | `str` | yes | Repo slug (usually derived from `repo_root` basename). |
| `rel_path` | `str` | yes | Repo-relative path associated with the memory (empty at repo root). |
| `confidence` | `low\|med\|high` | yes | How reliable the memory is (default: `med`). |
| `verification` | `str \| null` | no | Free-form proof/notes (example: `"ran pytest"`). |
| `created_at` | `str` (ISO-8601 datetime) | yes | Created timestamp (UTC, second precision). |
| `updated_at` | `str` (ISO-8601 datetime) | yes | Updated timestamp (UTC, second precision). |
| `error_signatures` | `list[str] \| null` | no | Error signature(s) the memory applies to (CLI: repeat `--error`). |
| `files` | `list[str] \| null` | no | Relevant file path(s) (CLI: repeat `--file`). |
| `commands_run` | `list[str] \| null` | no | Command(s) you ran to verify/fix (CLI: repeat `--cmd`). |

### Edit / remove

```bash
vibemem edit <uuid> --text "updated text" --tags "a,b"
vibemem rm <uuid>
```

### List

```bash
vibemem list --scope project --limit 20
vibemem list --scope global --type gotcha
vibemem list --scope all --tag python
```

### Sync (pull)

Rebuild local cache from Weaviate:

```bash
vibemem sync --pull --limit 200
```

Notes:
- “Push/offline queue” is a TODO stub (not implemented).

## Output modes

Default output is JSON:

```bash
vibemem scope
```

Pretty output:

```bash
vibemem --human scope
```

## Python API

VibeMem is also importable as a Python library. It uses the same config + scope model as the CLI, but the API lets you override scope explicitly when you want.

```python
import vibemem

# Recommended: a stateful client (reuses config + default scope)
vm = vibemem.VibeMem()
vm.add_memory(mem_type="recipe", text="Use X to fix Y", tags=["python", "typing"])
hits = vm.search_hits("TypeError: ...", top=8)

# Write to the global knowledge base (instead of the derived project scope)
vm.add_memory(mem_type="recipe", scope="global", text="Use X to fix Y", tags=["python", "typing"])

# Optional: set ownership / audience fields explicitly
vm.add_memory(
    mem_type="core",
    principal_type="shared",
    principal_id="global",
    bot_id=None,  # null applies to all bots
    text="Never output secrets or credentials; redact tokens.",
    tags=["safety"],
)
```

### Scope and granularity (what to pass when)

**Scope basics**

- Scope types: `"project"` or `"global"`.
- Project scope IDs look like `repo_slug` or `repo_slug::path/from/repo/root` (use forward slashes).
- Global scope ID is typically `"global"`.

Example (explicit scope targeting):

```python
# Assumes you already have a client:
# import vibemem
# vm = vibemem.VibeMem()

# Write to a specific project scope (not your current repo)
vm.add_memory(mem_type="recipe", scope="project", scope_id="otherrepo::a/b", text="Use X", tags="python")

# Search only that exact scope (no parent bubbling)
memories = vm.search_memories("TypeError", scope="project", scope_id="otherrepo::a/b", include_parents=False)
```

**Deriving a project scope ID**

If you don’t pass an explicit `scope_id`, VibeMem derives it from `cwd` (or `repo_root`):

- `granularity="repo"` (default): `myrepo`
- `granularity="cwd"`: `myrepo::a/b` (the full relative path)
- `granularity="path:N"`: `myrepo::a` (first `N` path parts)

**Per-call scope override parameters (client methods)**

These parameters apply to `vm.search*()` and `vm.add_memory()`:

- `scope="global"|"project"`: force the scope type for this call.
- `scope_id="..."`: explicitly target a specific scope ID (useful for “any repo/any path” scripts).
- `cwd=Path(...)` / `repo_root=Path(...)`: derive scope from a directory that isn’t your current working directory.
- `granularity="repo"|"cwd"|"path:N"`: affects derived project `scope_id` only (ignored if `scope_id` is provided).

**Ownership / audience parameters (client methods)**

These parameters apply to `vm.add_memory()` and `vm.edit_memory()`:

- `principal_type="user"|"bot"|"org"|"shared"`: who the memory belongs to.
- `principal_id="..."`: owner identifier (defaults to `$VIBEMEM_PRINCIPAL_ID` or your OS username when omitted on create).
- `bot_id="..."|None`: restrict to a specific bot (None applies to all bots).

Search-only parameters:

- `scope_ids=[...]`: search exactly these project scope IDs (no automatic parent bubbling).
- `include_parents=True|False`: when `scope_ids` is not provided, search current scope + parent scopes (default: `True`).
- `include_global=True|False`: when searching project scope, also include global results (default: `True`).

Other common parameters:

- `cache="auto"|"on"|"off"`: controls Chroma fallback/caching for `search` and cache updates for `add/edit/delete` (use `python -m pip install -U "vibemem[cache]"` for `"on"`).
- `tags=["a","b"]` or `tags="a,b"`: both forms are accepted by `add_memory()` / `edit_memory()`.

### Quick reference (client methods)

- `vm.search(query, ...) -> SearchResult`: includes `result.scope` (derived/overridden scope) and `result.hits` (scored `SearchHit`s).
- `vm.search_hits(query, ...) -> list[SearchHit]`: convenience wrapper returning just the hits.
- `vm.search_memories(query, ...) -> list[Memory]`: convenience wrapper returning just the `Memory` objects.
- `vm.add_memory(..., scope=..., scope_id=...) -> Memory`: create a memory in a specific scope.
- `vm.edit_memory(memory_id, ...) -> Memory`: edit by UUID (scope params are optional; the UUID identifies the memory).
- `vm.delete_memory(memory_id, ...) -> None`: delete by UUID.
- `vm.list_memories(scope="project|global|all", ...) -> list[Memory]`: list memories with server-side filters (scope here is a filter, not derived).
- `vm.scope_info() -> ScopeInfo`: show the derived default scope for the client.

### Convenience functions

For one-off scripts, module-level helpers create a temporary client under the hood (they accept the constructor-style parameters like `cwd=...`, `scope_type=...`, `scope_id=...`, `granularity=...`; `scope_type=` is the same idea as the per-call `scope=` on client methods):

```python
import vibemem

result = vibemem.search("TypeError: ...", top=8, granularity="cwd")
memories = vibemem.search_memories("TypeError: ...", top=8)
```

## Example agent prompt

Use something like this with your AI vibe coder to propose memories for your review before writing anything:

```text
You have access to this repository’s files. I want you to propose a list of “memories” for me to authorize before creating them.

1) Scan the repo for important environment information and setup details that would help in other projects (env vars, required services, ports, build tools, OS-specific steps, CI quirks, etc.).
2) Scan the repo for anything unusual, surprising, or easy to forget (non-obvious defaults, tricky edge cases, sharp corners, gotchas).
3) Output a list of candidate memories for approval. For each item, include:
   - type (recipe|gotcha|preference|note)
   - text (1–3 sentences)
   - suggested tags
   - scope suggestion (global vs project) and why
4) Do not create or write anything until I approve each memory.
```

## Notes

- The Weaviate collection will be auto-created on first use if it doesn’t exist.
- If the Weaviate instance doesn’t have a text vectorizer module configured, VibeMem will use a non-vectorized collection. Configure `VIBEMEM_EMBEDDING_HOST`/`PORT` to store vectors for semantic search; otherwise `search` falls back to BM25 keyword search.
