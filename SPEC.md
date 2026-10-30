# replay-store/v1 — spec (draft, name/version changeable)

Engine: **RevWright** — the index->file write/construction/refactor/REconstruction
engine (module `revwright`). Name is a temporary decision, like every decision
in this project: up for revision|review for goal progress.
Signal channel: see `SIGNAL.md` (signal/v1).

## object/v1
{"hash": "sha256[:16]", "content_ref": "objects/<hash>.json",
 "provenance": {"session_id": "uuid", "msg_idx": 0, "blk_idx": 0,
                "start_line": 0, "end_line": 0,
                "original_path": "metadata-only, non-binding"},
 "language": "optional", "sha_full": "sha256"}

## pointer/v1
{"session_id": "uuid", "msg_idx": 0, "blk_idx": 0, "content_hash": "sha256[:16]"}
Wire format must carry the full session id (legacy 12-byte truncation = gap G5, do not repeat).

## index/v1 (single structure, two directions)
{"forward": {"<session>:<msg>:<blk>": "<hash>"},
 "reverse": {"<hash>": ["<session>:<msg>:<blk>", "... 1:N"]}}

## recipe/v1 (a file)
{"path": "target path",
 "segments": [{"ptr": "pointer/v1"} | {"master_range": {"path": "...", "start": 0, "end": 0}}],
 "ops": [{"op": "before|after|around|in|customize|replace|drop|reorder",
          "target": "pointer/v1", "payload": "pointer/v1|null",
          "anchor": "inner anchor for `in`, else null"}]}

## history/v1 (per file, own tracking — replaces git log/blame)
{"recipe_hash": "sha256(recipe)", "parents": ["recipe_hash..."],
 "op_log": [{"op": "...", "target": "...", "payload": "...",
             "session_id": "editing session", "ts": "iso8601"}],
 "curator": "session/agent that authored this recipe version"}

## Invariants
- Every object resolves via reverse index; every pointer dereferences. (Round-trip test.)
- Replay(recipe) is deterministic: same recipe -> byte-identical file.
- No belongs-to check at import; fitness is judged at JIT compile / validation.
- Deletion fill: a missing object is filled only from a provenance extraction
  or a named validator copy, hash-verified — never invented.
