# REPLAY-001 (interim) — files as multi-message edit chains (2026-10-30)

Model (owner): a file = several edits across multiple messages/sessions.
Method: dedupe exports (9,603 entries) ⇒ group fenced blocks by `File:` target
⇒ order by (inserted_at, message_id) ⇒ per-file version chains. Ratios =
difflib SequenceMatcher (counts/ratios only; content stays local, gated).

## Chains found
- Targets with a `File:` marker: **44**; with ≥2 versions: **42**.
- `deepcli/deepcli/core.py` — 84 versions / 4 sessions; sim(first,last) = 0.246.
- `cli-synthegration/synthegration_index.py` — 20 versions / 2 sessions; sim(first,last) = 0.913.
- `test_script.py` (device path) — 38 versions / 34 sessions (prompt-embedded snapshots dominate).
- Unattached blocks (no in-message target): 21,009 raw ⇒ target attribution needs
  session-context inheritance (v0.2), not same-message markers only.

## Pending
- Oracle similarity sim(chain, master copy) for repo-resident targets —
  BLOCKED this pass: Collector bucket returned 403 (burst secondary limit
  after ~600 harvest calls). Retry after bucket reset; numbers land as
  REPLAY-001b. Chain-internal numbers above are unaffected.
