---
tags:
  - project
  - trust-systems
  - policy
  - opa
  - decision-trace
  - local-first
repo: steering
source_root: trust-systems/steering
---

# steering (trust-steering)

**Trust initiative** lab repo: **policy-bound** decisions, **traceable** operations, and **audit-ready** evidence—optimized for **local-first** iteration without ongoing cloud spend.

## Anchor flow

`HTTP → OPA policy → Decision Trace event → stream → worker → Evidence → OTel → exportable audit packet`

## Role in the ecosystem

- **Governance / proof layer** for *why* an action happened; orthogonal to [[punchcard-coder]] / [[punchcard-modelbase-mlx]] *inference* stacks unless you explicitly connect tool-calls or gateway routes to this pipeline.
- Shares themes with Kestrel docs: **observability**, **schemas**, **reproducible scripts**—integration potential is **contract design** (e.g. decision traces for privileged automation), not a built-in link today.

## Key links

- [[04_Source_Reference/Source_Document_Index#steering|Source `.md` index (table)]]
- [[02_Strategic_Views/Ecosystem_Integration_Analysis]]
- [[02_Strategic_Views/Gaps_and_Opportunities]]

## Source documentation (repository paths)

| Topic | Path |
|-------|------|
| Entry | `trust-systems/steering/README.md` |
| Repo map | `trust-systems/steering/docs/repo-map.md` |
| Decision Trace (narrative) | `trust-systems/steering/docs/decision-trace-schema.md` |
| Roadmap | `trust-systems/steering/docs/roadmap.md` |
| Threat model | `trust-systems/steering/docs/threat-model.md` |
| Control map / RMF | `trust-systems/steering/docs/control-map.md` |
| Audit packet | `trust-systems/steering/docs/audit-packet.md` |
