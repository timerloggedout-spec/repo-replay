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
rule discarded. ERRATUM (per-def %, assistant DB): _log_retry 98.5,
continue_response 99.9, send_message_working 100.0 — near-final, NOT
drifted; only chat_completion is drifted (23.9). Whole-file gain is
still only +0.8, so the remaining bottleneck is composition/order at
file level, not def fidelity. synthegration +3.8 from the same
relaxation. Attribution threshold is therefore a real pipeline stage
(L12): admission >=1, with fidelity handled by latest-order +
validator selection, not by exclusion.
