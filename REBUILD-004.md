# REBUILD-004 — per-def diagnostic for core.py (2026-10-30)

Latest-version vs master, per top-level def (25 total):

- **Byte-exact (1.000): 11 defs** — load_config, create_session,
  fetch_sessions, get_pow_challenge, wait_for_file, branch_conversation,
  continue_response, send_message_working, send_message, export_markdown
  (+1) — provenance chain complete for these.
- **Near (≥0.90): 8** — stream_completion .998, _log_retry .986,
  solve_pow .979, chat_completion .976, get_session .948, get_history .946,
  _cache_load .921, _set_last_session .909.
- **Drifted: 5** — export_json .617, save_config .305, _cache_save .227,
  get_token .155, _cache_path .132. Co-occurrence filtering (blocks with
  ≥2 core.py defs) does NOT fix them ⇒ not pool contamination: their final
  edits are absent from the harvested def pool — device-side edits
  (V3/V4 territory) ∨ unharvested exports. Sessions ≈ nearly-100%, and
  this is the measured remainder.
- **Gap: 1** — _session_cache_key (0 candidates).
