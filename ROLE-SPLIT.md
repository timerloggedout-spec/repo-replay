# ROLE-SPLIT — assistant | user | combined corpora (2026-10-30)

Owner order: reconstruction TARGET = ASSISTANT-only messages; USER rebuild
= separate database; combined = third database (results|methods union).
The mega-paste is a USER message ⇒ validation/user corpus, NOT target
material. DBs live in `repo-replay-data/db/`; the ☝🏽←→ pointer index now
carries kind categories (class | fn | method).

## WHOLE % (pipeline-v0.6 | role_split_auto)
| corpus | core.py | synthegration |
|---|---|---|
| assistant (TARGET) | 46.2 | 35.5 |
| user | 71.0 | 70.0 |
| combined | 71.0 | 75.1 |

## Gaps
- assistant x core.py: _session_cache_key, _log_retry, continue_response,
  send_message_working, chat_completion (5)
- user x core.py AND combined x core.py: _session_cache_key only
- synthegration: 0 gaps in all three corpora

## Pointer index by kind
- assistant (242): class 3, fn 185, method 54
- user (251): class 0, fn 156, method 95
- combined (493): class 3, fn 341, method 149

## Finding
The assistant-only target is far weaker than user-only on both files:
most recoverable bytes currently arrive via USER pastes (cat dumps,
mega-paste). Combined > either alone only on synthegration; ties user on
core.py. Assistant corpus holds ALL class-kind pointers (3); user holds
none but the most method rows. Honest read: today's scores were carried
by validation material; the target corpus needs export expansion
(assistant-side writes) to close the delta.

## Additional (lab queue)
1. role x channel matrix (% per corpus per channel: fence/raw/heredoc/cell)
2. thinking_content as a toggleable 4th corpus axis
3. per-role gap-cause split (L7 classes computed per corpus)
4. assistant-corpus enrichment = export expansion priority (owner: later)
