# REPLAY-001b — oracle similarity + corrections (2026-10-30)

## Oracle run (chain blocks vs master copies, Collector read)
| target | versions | exact | best block sim | last block sim | master bytes |
|---|---|---|---|---|---|
| deepcli/deepcli/core.py | 84 | 0 | 0.012 | 0.002 | 27,618 |
| cli-synthegration/synthegration_index.py | 20 | 0 | 0.026 | 0.002 | 25,030 |
| …/correlation/correlation_index.json | 28 | — | — | — | NOT ON MASTER (path drift) |

Finding: blocks under a `File:` marker are FRAGMENTS (edits, snippets,
discussion) — not full-file snapshots. Block-vs-file similarity ≈ 0.01–0.03
is therefore expected and meaningless alone; a file-level number requires
COMPOSITION (apply the chain in order) — replay v0.2 work, as the model
(file = several edits across messages) predicts.

## Correction — the 403
Earlier report said the harvest "depleted" the Collector bucket. WRONG:
primary quota was never near 5,000 (rate read 4,923 remaining before the
harvest window; ~600 calls total across two windows). The 403 was GitHub's
SECONDARY (burst) limit — request rate, not quota volume. Fix = pacing +
batching, applied in harvest v2.
