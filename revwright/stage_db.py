#!/usr/bin/env python3
"""RevWright stage database (v2: role-split corpora + kind-categorized pointer index) — every stage, per file, % by version|method.

SQLite store (data/stage_scores.db). One row per measurement:
  file | stage_version | method | item (WHOLE or class/def) | pct | source
`stage_db.py pivot <file>` renders items x (version|method) % columns.
Backfill rows carry their report of record in `source`; pipeline runs
append via record_run(). Scores are corpus-relative (L7)."""
import sqlite3, sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB = DATA_DIR / "stage_scores.db"  # combined corpus (default)

def db_for(corpus):
    """Owner role-split (2026-10-30): assistant = reconstruction TARGET,
    user = separate database, combined = union results|methods."""
    if corpus == "combined":
        return DB
    return DATA_DIR / f"stage_scores_{corpus}.db"
SCHEMA = """
CREATE TABLE IF NOT EXISTS stage_scores (
  file TEXT NOT NULL, stage_version TEXT NOT NULL, method TEXT NOT NULL,
  item TEXT NOT NULL, pct REAL, source TEXT,
  PRIMARY KEY (file, stage_version, method, item));
CREATE TABLE IF NOT EXISTS pointer_index (
  content_hash TEXT NOT NULL, kind TEXT NOT NULL, name TEXT NOT NULL,
  class_context TEXT, file_hint TEXT, session TEXT, msg TEXT, channel TEXT,
  PRIMARY KEY (content_hash, kind, name, session, msg, channel));
"""

# Backfill: only numbers actually measured and published (REBUILD-001..005,
# PIPELINE-001..003, V0-TEST). pct = similarity x100, 1 decimal.
BACKFILL = [
    # core.py — WHOLE file, by stage/method
    ("deepcli/deepcli/core.py", "hand-v0", "monolith_dump", "WHOLE", 35.0, "REBUILD-001"),
    ("deepcli/deepcli/core.py", "hand-v0", "heredoc_draft", "WHOLE", 55.2, "REBUILD-001"),
    ("deepcli/deepcli/core.py", "hand-v0", "append_compose", "WHOLE", 52.8, "REBUILD-003"),
    ("deepcli/deepcli/core.py", "hand-v0", "ordered_first_found", "WHOLE", 58.6, "REBUILD-003"),
    ("deepcli/deepcli/core.py", "hand-v0", "latest_pieces", "WHOLE", 65.8, "REBUILD-003"),
    ("deepcli/deepcli/core.py", "hand-v0", "latest_all_defs", "WHOLE", 68.6, "REBUILD-003"),
    ("deepcli/deepcli/core.py", "pipeline-v0.3", "auto_latest", "WHOLE", 71.0, "PIPELINE-001"),
    ("deepcli/deepcli/core.py", "pipeline-v0.4", "auto_latest", "WHOLE", 71.0, "PIPELINE-002"),
    ("deepcli/deepcli/core.py", "pipeline-v0.5", "auto_latest", "WHOLE", 71.0, "PIPELINE-003/V0-TEST"),
    # core.py — per-def, latest-version (fence pool; REBUILD-004 diagnostic)
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "_session_cache_key", None, "REBUILD-004 (gap)"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "_cache_path", 13.2, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "_cache_load", 92.1, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "_cache_save", 22.7, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "_set_last_session", 90.9, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "load_config", 100.0, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "save_config", 30.5, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "get_token", 15.5, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "get_session", 94.8, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "solve_pow", 97.9, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "create_session", 100.0, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "fetch_sessions", 100.0, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "get_history", 94.6, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "get_pow_challenge", 100.0, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "upload_file", 79.5, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "wait_for_file", 100.0, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "branch_conversation", 100.0, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "_log_retry", 98.6, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "stream_completion", 99.8, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "continue_response", 100.0, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "send_message_working", 100.0, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "send_message", 100.0, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "chat_completion", 97.6, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "export_markdown", 100.0, "REBUILD-004"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_fence", "export_json", 61.7, "REBUILD-004"),
    # core.py — per-def corrections via raw-segment channel (REBUILD-005)
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_raw", "export_json", 100.0, "REBUILD-005"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_raw", "get_token", 50.0, "REBUILD-005"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_raw", "save_config", 39.0, "REBUILD-005"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_raw", "_cache_path", 13.2, "REBUILD-005"),
    ("deepcli/deepcli/core.py", "hand-v0", "per_def_latest_raw", "_cache_save", 22.7, "REBUILD-005"),
    # synthegration_index.py — WHOLE
    ("cli-synthegration/synthegration_index.py", "hand-v0", "heredoc_direct", "WHOLE", 29.4, "REBUILD-005"),
    ("cli-synthegration/synthegration_index.py", "hand-v0", "class_compose", "WHOLE", 35.9, "REBUILD-005"),
    ("cli-synthegration/synthegration_index.py", "pipeline-v0.3", "auto_latest", "WHOLE", 25.9, "PIPELINE-001"),
    ("cli-synthegration/synthegration_index.py", "pipeline-v0.4", "auto_ops", "WHOLE", 32.3, "PIPELINE-002"),
    ("cli-synthegration/synthegration_index.py", "pipeline-v0.5", "auto_context", "WHOLE", 75.1, "PIPELINE-003/V0-TEST"),
    # synthegration_index.py — per class
    ("cli-synthegration/synthegration_index.py", "hand-v0", "whole_class_latest", "Pointer", 81.3, "REBUILD-005"),
    ("cli-synthegration/synthegration_index.py", "hand-v0", "whole_class_latest", "TaxonomyNode", 100.0, "REBUILD-005"),
    ("cli-synthegration/synthegration_index.py", "hand-v0", "rename_op", "_TaxonomyNode_v1", 100.0, "REBUILD-005"),
    ("cli-synthegration/synthegration_index.py", "hand-v0", "composite", "_CodexIndex_v1", 51.0, "REBUILD-005"),
    ("cli-synthegration/synthegration_index.py", "hand-v0", "method_compose", "CodexIndex", 21.1, "REBUILD-005"),
    ("cli-synthegration/synthegration_index.py", "pipeline-v0.5", "composite_context", "MessageIndex", 98.0, "PIPELINE-003"),
    ("cli-synthegration/synthegration_index.py", "pipeline-v0.5", "composite_context", "_CodexIndex_v1", 88.2, "PIPELINE-003"),
    ("cli-synthegration/synthegration_index.py", "pipeline-v0.5", "composite_context", "CodexIndex", 57.4, "PIPELINE-003"),
    ("cli-synthegration/synthegration_index.py", "pipeline-v0.5", "composite_context", "Pointer", 80.6, "PIPELINE-003 probe"),
]

def connect(db_path=DB):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    return con

def record(con, rows):
    con.executemany(
        "INSERT OR REPLACE INTO stage_scores VALUES (?,?,?,?,?,?)", rows)
    con.commit()

def record_index(rows, db_path=DB):
    """rows: (content_hash, kind, name, class_context, file_hint, session, msg, channel).
    kind categories: class | fn | method (owner order: the index holds kinds)."""
    con = connect(db_path)
    con.executemany("INSERT OR REPLACE INTO pointer_index VALUES (?,?,?,?,?,?,?,?)", rows)
    con.commit(); con.close()

def record_run(file, stage_version, method, whole_pct, per_item=None, source="run_pipeline", db_path=DB):
    con = connect(db_path)
    rows = [(file, stage_version, method, "WHOLE", whole_pct, source)]
    for item, pct in (per_item or {}).items():
        rows.append((file, stage_version, method, item, pct, source))
    record(con, rows)
    con.close()

def pivot(con, file):
    cols = con.execute(
        "SELECT DISTINCT stage_version, method FROM stage_scores WHERE file=? "
        "ORDER BY stage_version, method", (file,)).fetchall()
    items = [r[0] for r in con.execute(
        "SELECT DISTINCT item FROM stage_scores WHERE file=? "
        "ORDER BY (item='WHOLE') DESC, item", (file,)).fetchall()]
    vals = {(i, v, m): p for i, v, m, p in con.execute(
        "SELECT item, stage_version, method, pct FROM stage_scores WHERE file=?", (file,))}
    head = ["item"] + [f"{v}|{m}" for v, m in cols]
    lines = [" | ".join(head)]
    for it in items:
        row = [it]
        for v, m in cols:
            p = vals.get((it, v, m))
            row.append("GAP" if p is None and (it, v, m) in vals else (f"{p:.1f}" if p is not None else ""))
        lines.append(" | ".join(row))
    return "\n".join(lines)

if __name__ == "__main__":
    con = connect()
    if len(sys.argv) > 1 and sys.argv[1] == "backfill":
        record(con, BACKFILL)
        n = con.execute("SELECT COUNT(*) FROM stage_scores").fetchone()[0]
        print(f"backfilled; rows={n}")
    elif len(sys.argv) > 2 and sys.argv[1] == "pivot":
        print(pivot(con, sys.argv[2]))
    con.close()
