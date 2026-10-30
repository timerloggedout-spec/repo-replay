# SKELETON — v0.8/v0.8b skeleton-compose, assistant-only (2026-10-30)

Method: take a whole-file assistant draft as the skeleton (keeps header,
imports, inter-item material, order), replace each item span with the
latest pooled version; v0.8b also appends items that have no skeleton
span (v0.8 silently dropped them). Recorded in the assistant DB.

## WHOLE % (assistant corpus)
| file | v0.7 items | v0.8 skel blind/val | v0.8b skel blind/val |
|---|---|---|---|
| core.py | 47.0 | 51.6 / 51.6 | 52.1 / 52.1 |
| synthegration | 39.3 | 22.1 / 32.4 | 24.4 / 32.4 |

## Verdict
Skeleton-compose WINS on the fn-dominant file (core.py 47.0 -> 52.1;
blind latest skeleton == validator best, no oracle peeking needed) and
LOSES on the class-dominant file (39.3 item/context compose stands):
assistant skeleton drafts for synthegration are early and class-poor
(3 candidates), and appended classes lose inter-class context.
=> Method selection per file shape is a pipeline stage (L13):
skeleton for fn-files, context-compose for class-files; validator
arbitrates when both exist.
