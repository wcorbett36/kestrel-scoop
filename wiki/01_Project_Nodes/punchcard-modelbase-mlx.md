---
tags:
  - project
  - kestrel-systems
  - punchcard
  - mlx
  - openai-compatible
repo: punchcard-modelbase-mlx
source_root: kestrel-systems/punchcard-modelbase-mlx
---

# punchcard-modelbase-mlx

Thin **control plane** to make a Mac **MLX-ready**: curated model **rolodex** (`configs/models.yaml`), pinned tooling, and an **OpenAI-compatible** HTTP server (`/v1/chat/completions`, `/v1/models`, `/health`)—**not** the data plane (weights live in cache dirs, not in git).

## Role in the ecosystem

- **Consumer contract**: Punchcard uses provider `local_mlx` → `http://localhost:PORT/v1` (bind `0.0.0.0` so kind can use `host.docker.internal`).
- **Separation**: Application weights and caches are out-of-repo; repo stays a reproducible “operator” layer.
- Pairs with [[punchcard-coder]] conceptually as another local inference path; **no shared runtime**—integration is at **gateway + HTTP contract** level.

## Key links

- [[04_Source_Reference/Source_Document_Index#punchcard-modelbase-mlx|Source `.md` index (table)]]
- [[02_Strategic_Views/Ecosystem_Integration_Analysis]]

## Source documentation (repository paths)

| Topic | Path |
|-------|------|
| Entry | `kestrel-systems/punchcard-modelbase-mlx/README.md` |
| Control-plane overview | `kestrel-systems/punchcard-modelbase-mlx/OVERVIEW.md` |
| Operations | `kestrel-systems/punchcard-modelbase-mlx/quickstart.md` |
| Punchcard wiring | `kestrel-systems/punchcard-modelbase-mlx/docs/punchcard/README.md` |
| Adapters | `kestrel-systems/punchcard-modelbase-mlx/adapters/README.md` |
