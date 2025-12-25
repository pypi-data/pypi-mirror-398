# VibeMem usage rules for coding agents

Use VibeMem as the project’s “memory layer” while working with the user: retrieve relevant context before you start, and write back new learnings so future work improves.

## Required workflow: start every user task with VibeMem

Before you write a plan, edit files, or run implementation commands:

1. Check the current derived scope:
   - `vibemem scope`
2. Search for task-relevant memories:
   - `vibemem search "<task summary / key nouns>" --top 8`
3. If an error is involved, search the exact error text too:
   - `vibemem search "<exact error message>" --top 8`

Apply results as “local documentation”:
- Prefer memories from the current scope; use parent/global memories when relevant.
- If memories conflict, ask the user which one is current, then update the memory (`vibemem edit`) once clarified.
- If nothing relevant exists, proceed normally (but be prepared to write new memories as you learn).

If VibeMem is unavailable/misconfigured:
- Say so explicitly, run `vibemem config show` to confirm, ask the user whether to proceed without it, then continue with best effort.

## Required workflow: write new documentation whenever you learn something

Whenever you learn something you didn’t inherently know and it’s likely to matter later for this repo/user, add or update a VibeMem memory immediately (or at least before ending the task).

Examples of “new learnings” worth storing:
- Repo-specific facts (architecture, services, endpoints, conventions, internal tooling).
- User/team preferences (libraries, style rules, testing expectations, formatting choices).
- Version-specific behavior changes you had to discover (new syntax/behavior in a library version).
- Non-obvious fixes/recipes (especially if you had to try multiple approaches).
- Gotchas that caused failures (missing dependency, OS quirk, CI behavior, flaky test pattern).

Don’t store generic programming knowledge. Store durable, decision-relevant information that will save time later.

### Memory types

Use `--type`:
- `core`: “Non-negotiable” rules/invariants (use rarely and deliberately)
- `preference`: “Do it this way” (team/user choices)
- `recipe`: “Steps that work” (repeatable procedure)
- `gotcha`: “This breaks” (pitfall + fix/workaround)
- `finding`: “Fact about the system” (infra, layout, constraints)

### Writing a high-quality memory

Include:
- The punchline in the first sentence.
- Enough context to recognize when it applies (component, version, environment).
- Evidence when available: commands run, files touched, error signatures, verification.

Useful fields (repeatable where supported):
- `--error "<exact error signature>"`
- `--file "<path>"`
- `--cmd "<command you ran>"`
- `--verification "<how you verified>"` (e.g., “ran pytest”, “build succeeded”, “integration test passed”)

Avoid:
- Secrets (API keys, tokens), private credentials, or sensitive URLs. Redact/generalize.

### Tagging

Use consistent, searchable tags like `python`, `node`, `db`, `weaviate`, `otel`, `logging`, `ci`, `docker`, plus repo-specific tags (service/package names) when helpful.

## Common commands

- Search: `vibemem search "<query>" --top 8`
- Add: `vibemem add --type <core|finding|recipe|gotcha|preference> --text "<statement>" --tags "a,b,c" --confidence <low|med|high> --verification "<evidence>"`
- Edit (preferred over duplicates): `vibemem edit <uuid> --text "<updated statement>" --tags "a,b,c"`
- Browse: `vibemem list --scope project --limit 20`

## Examples of what to store

- Library version gotcha:
  - `vibemem add --type gotcha --text "Library X vY changed <old behavior> to <new behavior>; update <file/usage> accordingly." --tags "library-x,versioning" --confidence high --verification "confirmed in docs / ran tests"`
- User preference (e.g., Loguru over stdlib logging):
  - `vibemem add --type preference --text "Prefer Loguru over Python's standard logging for new/updated code in this repo." --tags "python,logging,style" --confidence high --verification "stated by user"`
- Repo/infra fact (e.g., OpenTelemetry endpoint):
  - `vibemem add --type finding --text "This repo uses OpenTelemetry; OTLP endpoint is http://x.x.x.x:4317 (gRPC) and is configured via <ENV_VAR/CONFIG>." --tags "otel,observability,infra" --confidence med --verification "seen in config"`

## End-of-task memory sweep (always)

Before you respond with “done”, check whether you learned anything new about this repo/user/tooling or encountered a failure that took time to diagnose. If yes, write/update the relevant VibeMem memories.
