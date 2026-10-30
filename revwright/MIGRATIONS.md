# RevWright — AppID method (scaffold, 2026-10-30)

Owner order 2026-10-30: migrations + replays use the AppID method going forward.

| Role | App | Bucket | Used for |
|---|---|---|---|
| Collector | Termux Fleet Collector `5535733` | own 5000/h | reads: harvest, census, migration sources |
| Publisher | Termux Fleet Publisher `5537873` | own 5000/h | writes: landings, PRs, migration targets |

Modules: `appid.py` (mint via fleet connector helpers, 0600 token files,
never printed) · `harvest.py` (Collector reads -> extract.py) ·
`publish.py` (Publisher writes: branch -> files -> PR).

Scope: both apps installed on `timerloggedout-spec/termux-monorepo` ∧
`timerloggedout-spec/repo-replay` (verified 2026-10-30T09:53Z ↦ GET
/installation/repositories on both app tokens; Collector read of
repo-replay from this lane ↦ 4 paths). PAT-fallback flag DROPPED for
these routes. Publisher has NO issues permission: coordination via PR
reviews, not issue comments.
