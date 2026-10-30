# STAGE-DB — every stage, per file, % by version|method (2026-10-30)

Store: `data/stage_scores.db` (SQLite) via `revwright/stage_db.py`.
Row = (file, stage_version, method, item, pct, source). `pct` = similarity
×100 (corpus-relative, L7); NULL pct = measured GAP. Every pipeline run
appends its stage rows (`record_run`); backfill carries only numbers
actually measured in REBUILD-001..005 / PIPELINE-001..003 / V0-TEST, each
with its report of record in `source`.

Render: `python3 revwright/stage_db.py pivot <file>` → items ×
(version|method) columns.

## deepcli/deepcli/core.py — WHOLE row
hand-v0: monolith 35.0 · heredoc_draft 55.2 · append 52.8 · ordered 58.6 ·
latest_pieces 65.8 · latest_all 68.6 → pipeline v0.3/v0.4/v0.5 auto: **71.0**
Per-def columns (fence vs raw channel) expose exactly where the raw
channel wins: export_json 61.7 → **100.0**, get_token 15.5 → 50.0,
save_config 30.5 → 39.0. `_session_cache_key` = GAP in every column.

## cli-synthegration/synthegration_index.py — WHOLE row
hand-v0: heredoc_direct 29.4 · class_compose 35.9 → v0.3 auto 25.9 ·
v0.4 auto_ops 32.3 · v0.5 auto_context **75.1**. Per-class v0.5 composite
column: MessageIndex 98.0 · _CodexIndex_v1 88.2 · CodexIndex 57.4 ·
Pointer 80.6 · TaxonomyNode 100.0 (whole-class) · _TaxonomyNode_v1 100.0
(rename_op).
