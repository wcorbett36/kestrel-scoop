---
tags:
  - project
  - active
  - kestrel-systems
  - obsidian
  - cli
repo: kestrel-scoop
source_root: kestrel-systems/kestrel-scoop
last_updated: 2026-04-05
---

# kestrel-scoop

**K-Compiler (Strategic Edition)** — CLI pipeline that maps and indexes local **Artemis** ecosystem repos, incrementally scrapes markdown, and (optionally) synthesizes **ProjectProfile** / strategic views into this vault via `src/synthesizer.py` and `src/obsidian.py`.

## Pipeline

1. **DocCrawler** — `**/*.md` from paths in `config.yaml`
2. **ManifestTracker** — SHA-256 in `.kb_manifest.json` to skip unchanged files
3. **Synthesizer** — `litellm` + Pydantic structured outputs (chunked when `chunk_repo_synthesis: true`)
4. **Obsidian formatter** — outputs to `./wiki/`

## Configured projects (see `config.yaml`)

| Project name | Path (relative to scoop root) | Focus |
|--------------|-------------------------------|--------|
| artemis_home | `../../artemis_home` | Core steering / architecture |
| kestrel-systems | `../../kestrel-systems` | Workflow tooling, gateways |
| repo_strategy | `../../repo_strategy` | DecisionOps strategy |
| trust-systems | `../../trust-systems` | Policy, OPA, security layers |

Run from repo root: `export PYTHONPATH=$(pwd)` then `python src/cli.py build` (after `.env` and venv setup per README).

## Related vault pages

- [[04_Source_Reference/Source_Document_Index]]
- [[02_Strategic_Views/Ecosystem_Integration_Analysis]]
- [[00_Home]]

## Source documentation

| Path |
|------|
| `kestrel-systems/kestrel-scoop/README.md` |
| `kestrel-systems/kestrel-scoop/ROADMAP.md` |
