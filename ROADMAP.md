# Roadmap

## Chunked repo synthesis (MLX / local LLMs)

**Problem:** `build` concatenates every changed markdown file in a project into one prompt and calls `synthesize_node` once. Large repos exceed context window and stall or fail on on-device models (e.g. MLX).

**Direction:** Keep **one `ProjectProfile` per repo** for downstream output and cross-repo synthesis, but **split ingestion**:

1. **Map:** Per file (or per batch under a token budget), call the LLM to produce a small structured artifact—chunk summary, topics, local gaps—using a dedicated schema or freeform text.
2. **Reduce:** Merge chunk outputs into a single `ProjectProfile` via a final LLM call and/or deterministic merge plus optional polish pass.

**Cross-repo:** `synthesize_view` already aggregates **profiles** (not raw docs). After chunking, enrich inputs if useful (e.g. include `dependencies`, `tags`) while staying within token limits.

**Other:** Persist per-chunk or per-file summaries in manifest/sidecars so unchanged files skip re-summarization; add config flags for max tokens per chunk and batch size.

**Config (implemented):** Top-level `chunk_repo_synthesis` (default `true`) and `max_chunk_chars` (default `48000` when omitted). Set `chunk_repo_synthesis: false` for single-shot prompts (e.g. large-context cloud models).

## Build resiliency (implemented)

Fail-fast `build` with structured errors (`BuildError` / `SynthesisStep`), optional **`GET /health`** when `OPENAI_API_BASE` is set (`--skip-preflight` to bypass), **`LLM_MAX_RETRIES`** for transient LLM connection failures, and **`K_COMPILER_DEBUG`** for tracebacks. Follow-up: `--continue-on-error` best-effort mode (see plan).

## Next steps

**Higher impact**

- **Hierarchical or batched reduce:** Very large repos can still overflow the **single** merge prompt (all chunk summaries). Merge in **layers** (batch N summaries → intermediate, repeat) or cap reduce input with deterministic trimming until one `ProjectProfile`.
- **`--continue-on-error`:** Best-effort build: stub failed projects, **do not** `update_record` for those source files so the next run retries; run **`synthesize_view`** on successful profiles only; log failures clearly.
- **Per-chunk / per-file map cache:** Persist map outputs keyed by content hash (sidecar JSON or manifest extension) so unchanged files skip **map** LLM calls on incremental builds.

**Medium**

- **Richer `synthesize_view`:** Pass **`dependencies`** and **`tags`** from each `ProjectProfile` when token budget allows.
- **Smoke / CI:** Minimal config (e.g. one README) plus **`--skip-preflight`** and mocked LLM, or a dry-run path, to catch CLI/parser regressions without MLX.
- **Observability:** Structured logging (project, step, duration, retry count) alongside existing Rich panels.

**Smaller**

- **Repo convention:** Decide whether **`./wiki`** is committed or gitignored; document in README.
- **Token budgets:** Optional **`tiktoken`** (or similar) to replace rough **char** limits with **token** limits where it matters.
