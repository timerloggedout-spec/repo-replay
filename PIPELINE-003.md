# PIPELINE-003 — v0.5: class-context attribution (2026-10-30)

**L11 (new stage):** method segments inherit the nearest preceding class
header — phase-tolerant (cell drift clips headers: `s MessageIndex:`).
Name-keyed assembly alone mixes classes (MessageIndex 0.169); with class
context the same segments compose at **0.980**.

## Automated corpus run (95s)
- core.py: **0.710**, gap `_session_cache_key` (UNRESOLVED, L7).
- synthegration_index.py: **0.751, gaps ∅** — all 6 classes recovered:
  Pointer (latest/context) · TaxonomyNode 1.000 · _TaxonomyNode_v1 rename
  1.000 · _CodexIndex_v1 composite 0.882 · CodexIndex composite 0.574 ·
  MessageIndex composite **0.980**. Ladder for this target: 0.259 (v0.3)
  → 0.323 (v0.4 ops) → 0.751 (v0.5 context).
