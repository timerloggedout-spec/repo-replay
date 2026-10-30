# REBUILD-001 — rebuilding test on discovered sessions (2026-10-30)

Corpus: `.deepcli/session_store/Request for additional files_3f3d5af3.json`
(16 msgs) — discovered via API code search for the file's own docstring.
Oracle: master `deepcli/deepcli/core.py` (27,618 B, cached locally).

## The delivery channels found (¬ plain fences)
1. **Terminal dumps** (USER paste): msg 27 `cat` output carries 3 whole files:
   `deepcli.py` monolith 23,783 chars · `deepapi.py` 5,586 · `investigate.py` 7,396.
   Corpus-wide census: 62 cat-dumps / 14 distinct targets.
2. **Heredoc write-scripts** (ASSISTANT): msg 28's bash block writes the
   refactored package via `cat > path << EOF`:
   `deepcli/__init__.py` 330 · `deepcli/core.py` 11,438 · `deepcli/cli.py` 9,864 · shim 226.

## Similarity vs oracle
- Monolith `deepcli.py` (msg 27) vs master core.py: **0.350** (ancestor; core is a split of it).
- Heredoc `deepcli/core.py` (msg 28) vs master core.py: **0.552** — a genuine
  partial ancestor: first refactor draft; master grew in later sessions.
- Owner's read confirmed: the content IS in the chats, delivered as dumps +
  heredoc scripts. Expansion with more exports (owner: later) should close
  the remaining ~45%.

## Extractor v0.2 requirements (derived)
- Adapters: cat-dump splitter (`~ $ cat <path>` segmentation) ∘ heredoc
  extractor (`cat > path << MARKER`) ∘ both feed the same recipe chain.
- Chain for core.py so far: monolith (msg 27) ⇒ split draft (msg 28) ⇒
  [later sessions pending export expansion] ⇒ master (oracle).
