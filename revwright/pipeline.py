#!/usr/bin/env python3
"""RevWright pipeline v0.5 — generalized rebuild automation.

Lessons codified from the per-file calibration passes (REBUILD-001..005):
 L1 channels before fences: heredocs are extracted from RAW content
    (code containing ``` breaks naive fence parsing); cat dumps are a
    separate channel with role=validation_snapshot, never content ops.
 L2 heredoc/sed/awk = proposed_op; only validation snapshots confirm state.
 L3 items, not blocks: AST top-level items when parseable, else line-scan
    segments with progressive-trim parse (raw-content defs count).
 L4 latest-by-timestamp wins per item (validated: latest == best-match
    upper bound on core.py); append-compose fails, order matters.
 L5 classify every block: snapshot|fragment|dump|signal|discussion.
    Signal (grep inventories, JSON symbol indexes) is evidence, never bytes.
 L6 rename/composite detection: class pairs whose bodies match after
    name-normalization are rename-op candidates (proven: _TaxonomyNode_v1).
 L7 absence is measured, not assumed — and never over-read: a zero-mention
    item is absent from THIS corpus, nothing more. Provenance itself is
    PARTIAL: the origin capture broke (git init reference: first add/commit
    failed in bash + an `rm` removed material), so early state entered no
    durable record at all. Gap causes must be classified, not defaulted:
    {never_in_chat | lost_at_origin_capture | unharvested_provider |
     drifted_final_edit | UNRESOLVED}. refTemplates/ (00_Index/RECOVERY.md
    + SOURCE-MAP.md on master) is a surviving slice of that origin issue.
    (Proven: _session_cache_key, 0 mentions corpus-wide => cause UNRESOLVED,
    NOT "written on-device only".)
 L8 hints are untrusted input: File:/path hints include template junk
    (`{target_file}`, `$target"`) — sanitize or the census fills with noise.
 L9 fixed-width cell pastes: terminal transcripts flattened into giant
    single lines of W-char padded cells (one cell = one output line).
    De-format by searching (offset, W) that maximizes AST parse + item
    count. Proven on 0efb156b msg21: a full sibling copy of
    synthegration_index.py (compression_sandbox) hides in this format.
 L10 ops are proposed, validators select: rename/composite ops are
    generated blind from pools; the validator (V1 master in tests)
    scores candidates — proposal and selection stay separate stages.
"""
import json, re, ast, difflib, hashlib
from pathlib import Path

FENCE = re.compile(r"```(\w*)\n(.*?)```", re.S)
HEREDOC = re.compile(r"cat\s*>\s*(\S+)\s*<<\s*\\?'?(\w+)\\?'?\n(.*?)\n\2\b", re.S)
CATDUMP = re.compile(r"~\s*\$\s*cat\s+(\S+)")
FILEMARK = re.compile(r"File:\s*(\S+)")
DEFSTART = re.compile(r"^(?:async\s+def|def|class)\s+(\w+)", re.M)
SIGNAL_HINTS = ('"sig":', 'def ', 'grep -n', 'funcfind')

def unesc(s):
    return s.replace("\\n", "\n") if s.count("\\n") > s.count("\n") else s

def norm_target(p):
    p = p.strip().strip('`')
    p = re.sub(r"^~?/", "", p)
    p = re.sub(r"^home/[^/]+/", "", p)
    if any(c in p for c in '{}$"\' ') or '..' in p:
        return None  # L8: template/placeholder junk is not a target
    if not re.match(r"^[\w.\-/]+$", p) or ('.' not in p and '/' not in p):
        return None
    return p

def channels(content):
    """Yield (channel, target_hint, text). L1: raw heredocs first."""
    out = []
    for path, marker, body in HEREDOC.findall(content):
        out.append(("heredoc_op", norm_target(path), body))
    parts = CATDUMP.split(content)
    for i in range(1, len(parts) - 1, 2):
        body = parts[i + 1].split("```")[0].strip()
        if body:
            out.append(("validation_snapshot", norm_target(parts[i]), body))
    marks = FILEMARK.findall(content)
    hint = norm_target(marks[0]) if marks else None
    for blob in content.split("\n"):
        if len(blob) > 2000 and "cat " in blob:
            starts = list(re.finditer(r"❯\s*cat\s+(\S+)", blob))
            for k, m in enumerate(starts):
                end = starts[k + 1].start() if k + 1 < len(starts) else len(blob)
                text = deformat_cells(blob[m.end():end])
                if text:
                    out.append(("cell_dump", norm_target(m.group(1)), text))
    for lang, code in FENCE.findall(content):
        out.append(("fence", hint, code))
    out.append(("raw", hint, content))
    return out

def classify(text, items_found):
    """L5 block classification."""
    lines = [l for l in text.split("\n") if l.strip()]
    if not lines:
        return "empty"
    sig = sum(1 for l in lines if '"sig":' in l or re.match(r"^\S+:\s+(def|class)\s", l))
    if sig >= 3:
        return "signal"
    if items_found and len(text) >= 4000:
        return "snapshot"
    if items_found:
        return "fragment"
    codeish = sum(1 for l in lines if l.startswith((" ", "\t", "def ", "class ", "import ", "from ", "#")))
    return "dump" if codeish / len(lines) > 0.6 else "discussion"

def top_items(src):
    """L3: AST top-level items {name: source} + header; {} if unparseable."""
    try:
        tree = ast.parse(src)
    except Exception:
        return {}, ""
    lines = src.split("\n")
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = "\n".join(lines[node.lineno - 1:node.end_lineno])
    hdr = "\n".join(lines[:tree.body[0].lineno - 1]) if tree.body else ""
    return out, hdr

def segment_items(text):
    """L3 fallback: line-scan top-level segments, progressive-trim parse."""
    lines = text.split("\n")
    starts = [i for i, l in enumerate(lines) if DEFSTART.match(l)]
    out = {}
    for k, i in enumerate(starts):
        j = starts[k + 1] if k + 1 < len(starts) else len(lines)
        name = DEFSTART.match(lines[i]).group(1)
        for end in range(j, i, -1):
            seg = "\n".join(lines[i:end]).rstrip()
            got, _ = top_items(seg)
            if name in got and len(got) == 1:
                out.setdefault(name, got[name])
                break
    return out

def items_of(text):
    got, hdr = top_items(text)
    if got:
        return got, hdr
    return segment_items(text), ""

_DEFORMAT_CACHE = {}

def deformat_cells(blob):
    """L9: recover line-structured text from fixed-width padded cells.
    Two-phase: cheap boundary score over (w, offset), then full segment
    extraction only for the best candidates. Memoized by blob hash."""
    import hashlib as _h
    key = _h.sha256(blob.encode()).hexdigest()
    if key in _DEFORMAT_CACHE:
        return _DEFORMAT_CACHE[key]
    cands = []
    for w in range(30, 101):
        for off in range(0, w):
            cells = [blob[i:i + w].rstrip() for i in range(off, len(blob), w)]
            text = "\n".join(cells)
            cheap = sum(1 for l in cells if DEFSTART.match(l) or l.startswith(("import ", "from ", "#")))
            cands.append((cheap, w, off, text))
    cands.sort(key=lambda x: -x[0])
    best = None
    for cheap, w, off, text in cands[:3]:
        n = len(segment_items(text))
        whole, _ = top_items(text)
        score = (n + 3 * len(whole), n)
        if best is None or score > best[0]:
            best = (score, text)
    result = best[1] if best and best[0][0] > 0 else None
    _DEFORMAT_CACHE[key] = result
    return result

def method_items(src):
    """{class: {method: source}} from a parseable source."""
    try:
        tree = ast.parse(src)
    except Exception:
        return {}
    lines = src.split("\n")
    out = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            out[node.name] = {
                ch.name: "\n".join(lines[ch.lineno - 1:ch.end_lineno])
                for ch in node.body
                if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return out

def rename_op(donor_src, new_name):
    """L10: rename a class declaration; body untouched."""
    return re.sub(r"class\s+\w+", f"class {new_name}", donor_src, count=1)

def composite_op(name, method_order, method_pool):
    """L10: assemble a class from latest method sources across contexts.
    method_pool: {method: [(ts, src, prov)]}. Returns (src, used, gaps)."""
    parts, used, gaps = [f"class {name}:"], {}, []
    for m in method_order:
        cands = method_pool.get(m, [])
        if not cands:
            gaps.append(m)
            continue
        ts, src, prov = max(cands, key=lambda x: x[0])
        parts.append(src)
        used[m] = prov
    return "\n\n".join(parts) + "\n", used, gaps

def reindent(src, base=4):
    """Normalize a def/class segment: head at `base` indent, body keeps
    its relative indentation. Returns None if it cannot be made to parse
    (wrapped in a dummy class when base > 0)."""
    lines = src.split("\n")
    if not lines:
        return None
    head_indent = len(lines[0]) - len(lines[0].lstrip())
    out = [" " * base + lines[0].lstrip()]
    for l in lines[1:]:
        if not l.strip():
            out.append("")
        else:
            ind = len(l) - len(l.lstrip())
            out.append(" " * max(base, base + ind - head_indent - 4 if head_indent else base + ind) + l.lstrip() if False else " " * (base + max(0, ind - head_indent - (4 if head_indent >= 4 else 0))) + l.lstrip())
    text = "\n".join(out)
    probe = ("class _Probe:\n" + text) if base else text
    try:
        ast.parse(probe)
        return text
    except Exception:
        return None

def context_segments(text):
    """L11: attribute method segments to the nearest preceding class
    header. Phase-tolerant: headers may be clipped by cell drift
    (`s MessageIndex:` for `class MessageIndex:`) or sit mid-line.
    Returns {(class_name | None, def_name): source} with defs normalized
    to a 4-space base when they parse, raw otherwise."""
    lines = text.split("\n")
    events = []  # (line_idx, kind, name)
    for i, l in enumerate(lines):
        m = re.search(r"class\s+(\w+)\s*:", l) or re.match(r"^\s{0,10}s\s+([A-Z]\w*)\s*:", l)
        if m:
            events.append((i, "class", m.group(1)))
            continue
        m = re.search(r"(?:async\s+def|def)\s+(\w+)\s*\(", l)
        if m:
            events.append((i, "def", m.group(1)))
    out = {}
    current_class = None
    for k, (i, kind, name) in enumerate(events):
        if kind == "class":
            current_class = name
            continue
        j = events[k + 1][0] if k + 1 < len(events) else len(lines)
        seg_lines = [l for l in lines[i:j] if "❯" not in l]
        while seg_lines and not seg_lines[-1].strip():
            seg_lines.pop()
        if not seg_lines:
            continue
        indents = [len(l) - len(l.lstrip()) for l in seg_lines if l.strip()]
        base = min(indents) if indents else 0
        norm = ["    " + seg_lines[0].lstrip()] + [
            ("    " + l[base:]) if l.strip() else "" for l in seg_lines[1:]]
        src = "\n".join(norm)
        key = (current_class, name)
        if key not in out:
            out[key] = src
    return out

def iter_messages(store_dir):
    seen = set()
    for f in sorted(Path(store_dir).glob("*.json")):
        try:
            data = json.loads(f.read_text(errors="replace"))
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for e in data:
            if not isinstance(e, dict) or not isinstance(e.get("content"), str):
                continue
            c = unesc(e["content"])
            h = hashlib.sha256(c.encode()).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            yield f.name, float(e.get("inserted_at") or 0), str(e.get("message_id")), e.get("role"), c

def build_pools(store_dir):
    """target -> {item: [(ts, src, prov)]} ; plus per-target channel census."""
    pools, census = {}, {}
    for fname, ts, mid, role, content in iter_messages(store_dir):
        for channel, hint, text in channels(content):
            if channel == "raw" and hint is None:
                continue
            items, _ = items_of(text)
            cls = classify(text, bool(items))
            key = hint or "(unattached)"
            census.setdefault(key, {}).setdefault(cls, 0)
            census[key][cls] = census[key].get(cls, 0) + 1
            if channel == "validation_snapshot":
                continue  # L2: snapshots validate, they are not op sources
            if hint is None:
                continue
            pool = pools.setdefault(hint, {})
            for name, src in items.items():
                pool.setdefault(name, []).append((ts, src, (fname, mid, channel)))
    return pools, census

def compose_latest(pool, order):
    """L4: latest version per item, emitted in `order`."""
    parts, used, gaps = [], {}, []
    for name in order:
        cands = pool.get(name, [])
        if not cands:
            gaps.append(name)
            continue
        ts, src, prov = max(cands, key=lambda x: x[0])
        parts.append(src)
        used[name] = prov
    return "\n\n".join(parts) + "\n", used, gaps

def rename_candidates(pools):
    """L6: same-body classes under different names across all pools."""
    by_norm = {}
    for target, pool in pools.items():
        for name, cands in pool.items():
            for ts, src, prov in cands:
                if src.startswith("class "):
                    norm = re.sub(r"class\s+\w+", "class X", src, count=1)
                    by_norm.setdefault(hashlib.sha256(norm.encode()).hexdigest(), set()).add(name)
    return [sorted(v) for v in by_norm.values() if len(v) > 1]

def sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()
