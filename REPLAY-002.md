# REPLAY-002 — compose v0.2 = NEGATIVE result + diagnosis (2026-10-30)

Naive compose (last snapshot-like block + splices) fails, quantified:
- core.py: composed 204,637 B vs master 27,618 B, sim 0.002.
- synthegration_index.py: composed 18,779 B vs master 25,030 B, sim 0.005.

Block census (why): across both chains, **0/104 blocks parse as complete
Python** (ast.parse). Median block = 2,462 B / 490 B; max = 102,348 B (a
multi-file dump). These chains contain NO full-file snapshot — the files
lived on-device and only fragments/diffs/snippets crossed the chat.

Implications (model update):
1. Composition target shifts: fragments compose onto a BASE obtained from a
   validator (V1/V2/V3) or from a session that DID paste the whole file —
   pointer-recipe = base-ref + ordered fragment ops, as SPEC already allows.
2. Block classification (snapshot|fragment|dump|discussion) is a required
   extractor stage BEFORE compose; size + parse + anchor tests derived here.
3. `files` metadata scan: **44 entries** carry non-empty files metadata
   (platform file ids + names, e.g. `test.txt`, a DeepSeek-web export) —
   attachment POINTERS exist; the content bytes are not in the export
   (platform-side storage), so not a local fill channel, but the pointers
   belong in the index. (Erratum: first publish of this report said 0 —
   the same-run scan said 44; corrected here.)
