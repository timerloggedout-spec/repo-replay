# V0-TEST — replay vs .git oracle (2026-10-30)

Protocol (SPEC V0): provision a test repo WITH `.git` as oracle/control;
delete the target files (the gap-fill case); reconstruct from Session
Provenance only (pipeline v0.5, no git objects read); measure the
remaining delta with git itself.

- Oracle commit: `53d42f6fd963` (2 files: deepcli/deepcli/core.py,
  cli-synthegration/synthegration_index.py).
- Deletion: both files removed from the worktree.
- Replay result: both files restored (status: modified, not deleted).
  - core.py sim vs git HEAD **0.710** (gap _session_cache_key, UNRESOLVED)
  - synthegration_index.py sim **0.751**, gaps ∅
  - `git diff --stat`: 283 insertions / 524 deletions across the 2 files —
    the honest remaining delta; the V0 goal (diff → 0) is now a measured
    quantity, not a claim.
- `git fsck --strict`: clean (rc 0). The oracle survives replay untouched;
  progressive .git corruption/removal tests build on this baseline.
