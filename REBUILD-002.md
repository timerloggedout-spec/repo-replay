# REBUILD-002 — the 0.448 hunt: piece map for core.py (2026-10-30)

Owner's framing: the msg-28 heredoc draft (sim 0.552) needs ≈0.448 more of
the file, as pieces in other messages. Function-level accounting vs master
`deepcli/deepcli/core.py` (36 defs/classes):

- Heredoc draft holds **19/36**.
- Missing 17 → **found in other messages: 9** · still missing: 8.
- Strong finds (5) sit in ONE mega-session (`0efb156b…`, 84 msgs): USER
  pastes up to 91,506 chars with 36–37 fences = multi-file dumps; the
  pieces (_log_retry, chat_completion, continue_response, send_message,
  send_message_working) are individual fences inside them. ⇒ extractor must
  split multi-file dumps fence-by-fence + attribute by def/class signature.
- Still missing (8): CurlRequestsFallback, DummyConsole, DummySession,
  MockCurlSession, _session_cache_key (+ generic post/put/print methods).
  The session-cache family is the coherent missing block — candidates for
  the owner's export expansion (later) ∨ validator fill (V2/V3).

Composition rule derived: base (validated snapshot ∨ heredoc draft) +
signature-attributed fragment ops, each op pending until a validation
snapshot (user cat dump) confirms the state.
