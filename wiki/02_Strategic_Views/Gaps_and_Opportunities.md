---
tags:
  - strategic-view
  - gaps
  - roadmap
last_updated: 2026-04-05
---

# Gaps and opportunities

Structured gap list derived from comparing **kestrel-systems** + **trust-systems** markdown: what is **not** specified, **inconsistent**, or **ripe for integration**.

## Documentation and inventory

| Gap | Detail | Opportunity |
|-----|--------|----------------|
| **Monorepo vs external Punchcard** | punchcard-coder docs assume a sibling **punchcard** repo; not present here. | Single “where Punchcard lives” note in this vault + link strategy (submodule, separate clone). |
| **kestrel-scoop config paths** | Projects include `artemis_home`, `repo_strategy`—optional paths. | Validate on CI or document “minimal required paths” for a full `build`. |
| **License** | punchcard-coder README has a placeholder license section. | Add SPDX / LICENSE file in repo and one line in project node. |
| **artemis_home** | Synthesized node may not match your local `artemis_home` tree. | Treat [[01_Project_Nodes/artemis_home]] as optional ingest; refresh when path exists. |

## Integration between inference and trust

| Gap | Detail | Opportunity |
|-----|--------|--------------|
| **No shared identity model** | Steering stresses subject/principal/correlation IDs; Punchcard coder API is **single-tenant / no auth** in v0. | Define a **future** pattern: JWT or mTLS from gateway → coder, map to Decision Trace `subject`. |
| **Two observability stories** | punchcard-coder: Grafana/Tempo/Ray URLs; steering: OTel + audit export. | One **correlation_id** convention across both for demos (doc + optional Helm values). |
| **Decision Trace for LLM tool use** | Not described in punchcard docs. | ADR: when a tool executes a side effect, emit a **Decision Trace** + **Evidence** per steering schemas. |

## Technical seams

| Gap | Detail | Opportunity |
|-----|--------|--------------|
| **Dual local inference paths** | GGUF/Ray vs MLX/OpenAI API—operators must choose. | Table in [[Ecosystem_Integration_Analysis]] (already started) + “when to use which” in punchcard docs. |
| **Kestrel-scoop LLM dependency** | Build uses configured LLM for synthesis; different from on-device MLX for products. | Keep `.env` and `config.yaml` samples aligned with [[punchcard-modelbase-mlx]] model ids where relevant. |

## Next steps (wiki maintenance)

- Re-run `python src/cli.py build` from [[01_Project_Nodes/kestrel-scoop]] after large doc edits so synthesized sections stay aligned.
- Add Dataview queries (optional plugin) on `tags: project` in `01_Project_Nodes/` if you want auto-lists on [[03_Maps/Index]].

Related: [[Global_Ecosystem_Status]], [[Ecosystem_Integration_Analysis]].
