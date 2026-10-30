# EXTRACT v0.1 — dual-key join + sensitivity gate (2026-10-30)

Implements HARVEST-001 requirements ∧ sensitivity-rules/v0.1 gates R1–R10.
Code: `revwright/{join,sensitivity}.py` (this PR). Run over HARVEST-001 corpus:

- Join: hash-key 18 ∘ (session,msg)-key 130 ⇒ **148/148 items resolved, gaps 0**
  (e102's 130 empty-hash objects recovered via the msg fallback, per design).
- Sensitivity gate (counts only, ∅ values): home_path 756 · bearer 19 ·
  kv_secret 45 · auth_hdr 4 · ipv4 3 · entropy 5 spans.
- Fail-closed: **3 items quarantined** (unclassified high-entropy) — held from
  any publish pending review, per ruleset.
- Provenance: published records carry sha_redacted + span {class, len_bucket};
  sha_orig lives ONLY in the restricted local sidecar (∅ published).
