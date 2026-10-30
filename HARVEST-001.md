# HARVEST-001 — conv_repo ⋈ session_store (2026-10-30)

Route: Collector AppID reads (termux-monorepo, read-only) ⇒ local join ⇒ this report.
Evidence: harvest run 2026-10-30 (this lane); counts firsthand from the harvested trees.

## Corpus
- `cli-synthegration/conv_repo`: 182 tree entries ⇒ 160 blobs; 11 sessions; 148 objects.
- `.deepcli/session_store`: 411 blobs listed, 408 files harvested (Δ3 = NOT ESTABLISHED, flagged).
- conv_repo objects carry metadata only: {message_id, parent_id, role, content_hash, ts} — ∅ content bytes.

## Join 1 — content_hash (sha256[:16] of message text)
- Distinct content_hash values across 148 objects: **13**.
- 9 tiny sessions (2 msgs each, 18 msgs total) resolve fully: real prompts + code
  (the `test_script.py` ZeroDivisionError refactor family + greeting tests).
- `baf42557` = branch stub, 0 msgs (known gap G2).

## Join 2 — the empty-hash gap ∧ (session, message_id) fallback
- Session `e102d768` ("Termux CLI Recon and Harmonization Commands", 130 objects):
  ALL 130 objects carry content_hash `e3b0c44298fc1c14` = sha256("")[:16] — a
  data-loss signature in that export, NOT resolution. (An earlier draft count of
  "148/148 resolved" was inflated by this collision; corrected here.)
- Content recovered anyway: session_store holds its export file
  (`..._e102d768.json`, 664 entries incl. thinking_content + files metadata),
  joinable on **(session, message_id)** — conv message_ids 1..130 ⊆ its ids.

## Extractor v0.1 requirements (derived)
1. Two join keys: content_hash (primary) ∘ (session, message_id) (fallback).
2. Empty-hash = GAP flag, never a resolution.
3. Per-exporter adapters: conv_repo (hash-only DAG) ∘ deepcli session_store
   (full entries, stringly-typed fields, title-named files exist).
