---
tags:
  - project
  - kestrel-systems
  - punchcard
  - local-first
  - ray
repo: punchcard-coder
source_root: kestrel-systems/punchcard-coder
---

# punchcard-coder

First canonical **Punchcard** workload: a **local-first**, repo-aware coding assistant (explain / generate / summarize) with deterministic, bounded context—no automatic RAG or agent loops in v0.

## Role in the ecosystem

- Sits on **Punchcard** infra: kind, Ray Serve, Traefik, OTel/Grafana stack (details in repo `docs/overview.md`, indexed below).
- **Model**: Qwen2.5-coder-7b (GGUF, q4_k_m), **llama.cpp** / Ray Serve; optional **host-external** execution for GPU/Metal via gateway to `host.docker.internal`.
- Complements [[punchcard-modelbase-mlx]]: coder is a **Ray/llama.cpp** path; modelbase is **MLX + OpenAI-compatible HTTP**—different stacks, both “local inference” options for Punchcard-shaped routing.

## Dependencies (documented)

- kind, KubeRay, Traefik, model weights (GGUF), Ray Serve entrypoints (`serve_entrypoint.py`, `src/punchcard_coder/`).

## Key links

- [[04_Source_Reference/Source_Document_Index#punchcard-coder|Source `.md` index (table)]]
- Related strategic view: [[02_Strategic_Views/Ecosystem_Integration_Analysis]]

## Source documentation (repository paths)

Paths are relative to the Artemis workspace root (`artemis/`).

| Topic | Path |
|-------|------|
| Entry | `kestrel-systems/punchcard-coder/README.md` |
| Architecture / deploy | `kestrel-systems/punchcard-coder/docs/overview.md` |
| Punchcard platform refs | `kestrel-systems/punchcard-coder/docs/punchcard/` |
| Feature spec | `kestrel-systems/punchcard-coder/docs/features/coder.md` |
| Tasks / status | `kestrel-systems/punchcard-coder/docs/tasks.md` |
| Model contract (Punchcard) | `kestrel-systems/punchcard-coder/docs/punchcard/punchcard-model-contract.md` |
