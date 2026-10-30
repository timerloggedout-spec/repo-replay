# PIPELINE-001 — per-file lessons ⇒ automation (2026-10-30)

Owner's redirect: the file-by-file passes were CALIBRATION. Their value is
the lessons, codified as general stages in `revwright/pipeline.py` (v0.3):
L1 raw-content channels before fences (inner ``` breaks fence parsing) ·
L2 cat dumps = validation_snapshot, heredoc/sed/awk = proposed_op ·
L3 item extraction: AST top-level ∘ line-scan segments (raw defs count) ·
L4 latest-by-timestamp per item, ordered compose (append fails) ·
L5 block classification snapshot|fragment|dump|signal|discussion ·
L6 rename/composite detection · L7 gap-cause classification (below).

## First automated corpus run (deduplicated messages, 93s)
- Census: 685 explicit-target channel sets; unattached = the signature
  pool. Hint noise observed (`{target_file}`, `$target"`) ⇒ hint
  sanitization is a required stage.
- **core.py: sim 0.710 FULLY AUTOMATED** (beats hand compose 0.686 — the
  generalized raw-segment channel recovers pieces the manual pass missed);
  items 24/25, gap `_session_cache_key`.
- **synthegration_index.py: sim 0.259 automated** vs 0.359 with manual
  rename/composite ops ⇒ op APPLICATION (not just detection) is the next
  automation stage.

## L7 correction (owner, 2026-10-30) — provenance is PARTIAL
Absence from the corpus ≠ "written on-device only". The origin capture
itself broke: in the git-init reference the first add/commit failed in
bash and an `rm` removed material, so early state entered NO durable
record. `refTemplates/` is a surviving slice of that noted issue (its
00_Index carries RECOVERY.md + SOURCE-MAP.md). Gap causes are therefore
classified {never_in_chat | lost_at_origin_capture |
unharvested_provider | drifted_final_edit | UNRESOLVED}; every current
gap, `_session_cache_key` included, is UNRESOLVED until signal classifies
it. All scores are corpus-relative, not absolute.
