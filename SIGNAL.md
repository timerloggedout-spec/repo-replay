# signal/v1 — non-code signal in session exports (SPEC amendment, queued)

Session exports carry more than code. User comments/messages embed command
output that is **structural signal** for reconstruction — a second,
independent evidence channel beside the code extractions themselves.

## Classes
- `layout` — `tree`, `ls -laR`, `find` output: path inventory; `ls -laR`
  also gives size / permissions / timestamps per file.
- `search` — `grep -r`, `rg`, code-search results: existence + location
  claims for symbols/files at a point in time.
- `exclusion` — ignore/exclusion lists (`.gitignore`-style, skip lists,
  "not these" enumerations): what was deliberately NOT in the repo.
- `env` — `bin/` listings, `alias`, `PATH`, `which`, env dumps: the runtime
  layout clues — what the JIT environment must reconstruct.

## signal/v1 record
{"class": "layout|search|exclusion|env",
 "cmd": "tree | ls -laR | grep ... | alias | PATH",
 "provenance": {"session_id": "uuid", "msg_idx": 0},
 "claims": [{"path": "...", "size": 0, "ts": "iso8601|null", "exists": true}],
 "raw_ptr": "pointer to the containing message block"}

## Uses (validation + training)
1. **Expected-tree oracle**: replay coverage = extracted paths vs layout
   claims. In a listing but not extracted = GAP. Absent everywhere +
   on an exclusion list = NOT a gap (deliberate). This is how a deletion
   (against the rules) is told apart from a never-included file.
2. **Version discrimination**: `ls -laR` size/ts is a weak fingerprint to
   pick between multiple LLM writes of the same block when hashes tie
   or content is missing.
3. **Validator tie-break**: when V1..V4 copies disagree, signal claims are
   timestamped third-party evidence inside the provenance record itself.
4. **Env reconstruction**: `env` signal defines the bin/PATH/alias layout
   the JIT compile step assumes.
5. **Training labels**: signal-vs-replay mismatches are labelled examples
   for the gap-fixing pipeline, same as G1..G8.

Signal is evidence, never content: a layout claim can prove a file
existed and its size, but cannot invent its bytes — fill still requires
an extraction or a validator copy, hash-verified.
