# REBUILD-005 — second target + core.py corrections (2026-10-30)

## Target 2: cli-synthegration/synthegration_index.py (oracle 25,030 chars)
Different failure mode than core.py:
- Direct whole-file writes: exactly **1 unique heredoc** (8,048 chars,
  e102 msg 146) sim **0.294** — an early version. Fence parsing initially
  missed it: the code itself contains ``` sequences, breaking naive fence
  splits ⇒ extractor must pull heredocs from RAW content.
- Class compose (oracle order, latest candidates + ops): **0.359**
  (vs 0.313 top-level-only). Per class: Pointer .813 · TaxonomyNode 1.000 ·
  _TaxonomyNode_v1 **1.000 via rename op** on TaxonomyNode (normalized
  sim 1.000 — cross-version rename composition works) · _CodexIndex_v1 .510
  as a COMPOSITE (oracle itself concatenates a v1 from_live_exports +
  Pointer's methods, byte-equal) · CodexIndex .211 (methods 9/16 in
  exact-context pools) · MessageIndex GAP as parseable class.
- The missing mass (CodexIndex 12,518 + MessageIndex 4,858 = 69% of file)
  exists as: grep/funcfind SIGNAL inventories (def names + line numbers,
  e.g. reverse_lookup @505), JSON symbol indexes (sandbox copy: CodexIndex
  @83+178, MessageIndex @424), and a **padded-column mega-paste**
  (0efb156b msg 21) current extractors cannot segment.
- Extractor requirements derived: raw-heredoc channel ∘ padded-paste
  de-formatting ∘ rename/composite class ops ∘ signal inventories as
  validation (line-number oracle), never content.

## core.py corrections to REBUILD-004
- **export_json: byte-exact (1.000) found** via raw-segment extraction
  (e2c05aa8 msg 9) — the fence pool had missed it. Exact defs now **12/25**.
- get_token best improves .155 → .500 (still drifted).
- _cache_path .132 / _cache_save .227 / save_config .390 stand: final
  bodies absent from corpus in every shape searched.
- **_session_cache_key: 0 mentions in the ENTIRE harvested corpus**
  (content + thinking_content, defs + call sites). The name never crossed
  a chat ⇒ written on-device only ∨ in unharvested provider sessions.
  This is the measured boundary of "nearly 100% from sessions".
