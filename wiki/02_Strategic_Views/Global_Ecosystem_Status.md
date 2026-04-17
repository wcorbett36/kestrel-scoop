---
tags:
  - strategic-view
  - Documentation
  - Knowledge Management
  - Artemis Ecosystem
  - Obsidian Wiki
last_compiled: '2026-04-05'
strategic_focus: State of documentation and cross-repo alignment
---

# Global ecosystem status

## Overview

The **Artemis** workspace combines **Kestrel** tooling (documentation synthesis, local inference adapters) and **Trust** tooling (policy, decision traces, evidence). This vault is generated and curated under `kestrel-scoop/wiki` so teams can browse relationships in **Obsidian** with consistent frontmatter and wikilinks.

**kestrel-scoop** implements `Source → Mirror → Synthesis → Generation`: crawl configured repos for markdown, track hashes in `.kb_manifest.json`, optionally call an LLM for structured profiles, and emit Obsidian-friendly pages.

## Repository status (high level)

| Repo | Role | Maturity (per docs) |
|------|------|------------------------|
| [[01_Project_Nodes/kestrel-scoop]] | Doc pipeline + this vault | Active; chunked synthesis for local LLMs |
| [[01_Project_Nodes/punchcard-coder]] | Punchcard workload (local coder API) | Active development; v0 scope explicit |
| [[01_Project_Nodes/punchcard-modelbase-mlx]] | MLX OpenAI-compatible host | Control-plane stable pattern |
| [[01_Project_Nodes/steering]] | Decision trace gateway lab | Scaffold + roadmap phases 0–5 |

## Where to go next

- Integration narrative: [[Ecosystem_Integration_Analysis]]
- Gaps and follow-ups: [[Gaps_and_Opportunities]]
- Full markdown path index: [[04_Source_Reference/Source_Document_Index]]

## Historical ecosystem gaps (superseded by deeper analysis)

Earlier notes mentioned only generic documentation fragmentation. See [[Gaps_and_Opportunities]] for a **repo-specific** gap list.
