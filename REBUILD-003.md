# REBUILD-003 — compose ladder for core.py (2026-10-30)

Similarity vs master `deepcli/deepcli/core.py`, by compose strategy:

| strategy | sim |
|---|---|
| monolith dump (validated state, msg 27) | 0.350 |
| heredoc draft alone (msg 28) | 0.552 |
| append-compose (pieces at end) | 0.528 ✗ order matters |
| ordered compose (master def order, first-found pieces) | 0.586 |
| ordered + latest-version pieces | **0.658** |
| ordered + latest version of EVERY def | **0.686** |

Findings:
- **Latest == best**: per-def, the latest-timestamped candidate version is
  also the closest to master (upper bound = latest pick, 0.658). Time-ordered
  composition needs no oracle peeking. ✓ methodology validated.
- Version pools are deep: get_token ×50, upload_file ×25, create_session
  ×21, solve_pow ×19 versions across the harvested sessions.
- Coverage 24/25 top-level defs. Sole gap: `_session_cache_key` — 0 def
  candidates in harvested exports (references only). Awaits export
  expansion ∨ validator fill.
- Remaining delta ≈ intra-def drift (final edits in unharvested sessions)
  + class-body evolution + inter-def module code.
