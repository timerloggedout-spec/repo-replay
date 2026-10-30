# ASSISTANT-FOCUS — v0.7 attribution relaxation (2026-10-30)

Owner focus: ASSISTANT-ONLY reconstruction. Experiment: pool admission
threshold >=2 known items -> >=1 (solo unhinted blocks admitted), all
other stages unchanged. Recorded in the assistant DB
(pipeline-v0.7 | attn_relaxed_assistant).

## Results (assistant corpus only)
| file | v0.6 | v0.7 | gaps v0.6 -> v0.7 |
|---|---|---|---|
| core.py | 46.2 | 47.0 | 5 -> 1 (_session_cache_key) |
| synthegration | 35.5 | 39.3 | 0 -> 0 |

## Read
The 4 missing defs (_log_retry, continue_response, send_message_working,
chat_completion) WERE present assistant-side — as solo blocks the >=2
rule discarded. Presence recovered; fidelity is the remaining problem:
whole-file gain is only +0.8, so the recovered copies are drifted
drafts, not finals (per-def % in the assistant DB). synthegration +3.8
from the same relaxation. Attribution threshold is therefore a real
pipeline stage (L12): admission >=1, with fidelity handled by
latest-order + validator selection, not by exclusion.
