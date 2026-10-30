# repo-replay

Owner-original system. No external integrations.

An alternative to `.git` built from **Session Provenance Code Extractions**:
the owner's session-chat code exports are the source of truth, and a repo is
a reconstruction from them — not a copy of a working tree.

## Model

- **Object** — an extracted code block, content-addressed (`sha256[:16]`),
  stored once, carrying its provenance `(session_id, msg_idx, blk_idx, lines)`.
- **Pointer** — file-agnostic reference to an object:
  `(session_id, msg_idx, blk_idx, content_hash)`. A block's original target
  file is provenance metadata, never a constraint.
- **Index** — one structure, two directions: forward
  `provenance -> object`, reverse `hash -> [pointer...]` (1:N mandatory).
- **Recipe** — a file. An ordered list of segments (pointers and/or
  master-ranges) plus composition ops. A file may be a curated aggregate of
  pointers from several responses that edited the same *or different* files.
  A collaborator may write a file with **only pointers** — zero new content;
  authorship = curation.
- **History** — our own tracking DAG (not git history). A file version is a
  recipe hash + parent recipe(s) + op log. Blame is intrinsic: every segment
  already carries its session.

## Composition ops (import customization, up to full refactor)

`customize(ref)` · `before(ptr, x)` · `after(ptr, x)` ·
`around(ptr, wrap)` · `in(ptr, x)` (sub-block anchor `ptr#inner:<anchor>`) ·
`replace` / `drop` / `reorder`.

## Validation

Test repos are provisioned **with** `.git` as oracle (V0): replay diff vs the
`.git` tree must go to 0; deletions inside the `.git` copy are gap-fill test
cases. Validators: V1 GitHub current (carries collaborator deletions made
against the rules — each is a fill test), V2 GitLab earlier copy
(`a-group2180532/termux-monorepo`), V3 Termux local on both devices,
V4 device Origin (first commit corrupted — graduation test: rebuild
everything prior from Session Provenance mapping only).

## End state

Chat-direct interface; dedup content-addressed storage with pointer-only
sync; **JIT compile from import index references** (lazy materialization of
reachable segments only); surgical pointer-addressed edits — block-granular,
hash-verified, atomic — for super-low token use, better than `sed`.

Spec: `SPEC.md` · Exported methods (imported by termux-monorepo): `METHODS.md`
