# PIPELINE-002 — v0.4: ops applied, new channel (2026-10-30)

New stages in `revwright/pipeline.py` (v0.4):
- **L8 hint sanitization**: target hints are untrusted — template junk
  rejected. Census targets 685 → **616 real** (noise removed).
- **L9 fixed-width cell channel**: terminal transcripts flattened into
  giant lines of W-char padded cells (W=59 proven). Two-phase de-format
  (cheap boundary score → segment extraction, memoized). On 0efb156b
  msg21 it recovers the compression_sandbox synthegration_index copy —
  21,936 chars, 15 method segments incl. the previously-missing
  `_rebuild_hash_index`, `chunk_similarity`, `load_export`,
  `reverse_lookup`, `search_tables`.
- **L10 ops proposed, validator selects**: rename_op + composite_op are
  generated blind from pools; the validator scores candidates.

## Automated run (106s, corpus-wide)
- core.py: **0.710** maintained; gap `_session_cache_key` (UNRESOLVED).
- synthegration_index.py: base 0.259 → **0.323 with ops**: rename op
  applied automatically (`_TaxonomyNode_v1` at 1.000 vs oracle).
- Remaining gaps: `_CodexIndex_v1`, `MessageIndex` — composite assembly
  from cell segments scores <0.30 (segment indentation lost in the cell
  format) ⇒ composite-v2 = re-indentation stage, next backlog.
