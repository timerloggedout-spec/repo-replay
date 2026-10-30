#!/usr/bin/env python3
"""RevWright sensitivity gate — sensitivity-rules/v0.1 (Forensic::preserve).
Detectors C1..C5 → spans (∅ values stored) → resolutions → redacted text +
restricted sidecar (sha_orig, local only) + publishable sha_redacted.
Fail-closed: unclassified high-entropy spans quarantine the item.
"""
import hashlib, json, math, re
from collections import Counter

PATTERNS = [
    ("C1", "gh_pat", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")),
    ("C1", "provider_key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("C1", "aws_key", re.compile(r"(AKIA|ASIA)[A-Z0-9]{16}")),
    ("C1", "jwt", re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
    ("C1", "privkey", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("C1", "bearer", re.compile(r"Bearer\s+\S{8,}")),
    ("C1", "url_query_secret", re.compile(r"[?&](key|token|secret|auth)=[^\s&]{6,}")),
    ("C2", "auth_hdr", re.compile(r"Authorization\s*[:=]\s*\S+")),
    ("C2", "cookie_hdr", re.compile(r"(Set-)?Cookie\s*[:=]\s*[^\n;]{4,}")),
    ("C3", "email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("C3", "ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("C3", "home_path", re.compile(r"(/home/|/Users/|/data/data/com\.termux/files/home/)([A-Za-z0-9._-]+)")),
]
KV = re.compile(r"(api_key|secret|token|password)\s*[:=]\s*['\"]?([^\s'\"]{8,})", re.I)
TOKEN = re.compile(r"[A-Za-z0-9_\-]{24,}")
DEFAULT_RES = {"C1": "vault_or_redact", "C2": "redact", "C3": "redact",
               "C4": "use", "C5": "span_rules", "ENTROPY": "archive"}

def entropy(s: str) -> float:
    c = Counter(s); n = len(s)
    return -sum((v / n) * math.log2(v / n) for v in c.values())

def len_bucket(n: int) -> str:
    return "s" if n < 16 else "m" if n < 64 else "l" if n < 256 else "xl"

def scan(text: str):
    """Return (spans, counts). Span = {start,end,class,detector} — ∅ value."""
    spans, counts = [], Counter()
    covered = []
    def taken(a, b): return any(a < y and b > x for x, y in covered)
    for cls, det, rx in PATTERNS:
        for m in rx.finditer(text):
            a, b = (m.start(2), m.end(2)) if det == "home_path" else (m.start(), m.end())
            if taken(a, b): continue
            covered.append((a, b)); counts[det] += 1
            spans.append({"start": a, "end": b, "class": cls, "detector": det})
    for m in KV.finditer(text):  # C1 two-stage: shape ∧ ¬ placeholder/code-ref
        val = m.group(2)
        if val.lower() in {"none", "null", "true", "false"} or val.startswith(("os.", "process.", "${")): continue
        a, b = m.start(2), m.end(2)
        if taken(a, b): continue
        covered.append((a, b)); counts["kv_secret"] += 1
        spans.append({"start": a, "end": b, "class": "C1", "detector": "kv_secret"})
    for m in TOKEN.finditer(text):  # entropy gate → unclassified quarantine class
        s = m.group(0)
        if taken(m.start(), m.end()): continue
        if entropy(s) >= 4.2 and any(c.isdigit() for c in s) and any(c.isalpha() for c in s):
            counts["entropy"] += 1
            spans.append({"start": m.start(), "end": m.end(), "class": "ENTROPY", "detector": "entropy"})
    return sorted(spans, key=lambda s: s["start"]), counts

def redact(text: str, spans):
    out, last = [], 0
    for i, sp in enumerate(spans):
        out.append(text[last:sp["start"]])
        out.append(f"⟦REDACTED:{sp['class']}:s{i}:{len_bucket(sp['end']-sp['start'])}⟧")
        last = sp["end"]
    out.append(text[last:])
    return "".join(out)

def process(ptr: str, text: str):
    """Gate one item. Returns (record, redacted_text, quarantined)."""
    spans, counts = scan(text)
    red = redact(text, spans)
    quarantined = any(sp["class"] == "ENTROPY" for sp in spans)
    record = {
        "ptr": ptr,
        "sha_redacted": hashlib.sha256(red.encode()).hexdigest()[:16],
        "counts": dict(counts),
        "spans": [{"span_id": f"s{i}", "class": sp["class"], "detector": sp["detector"],
                   "len_bucket": len_bucket(sp["end"] - sp["start"])} for i, sp in enumerate(spans)],
        "quarantined": quarantined,
    }
    sidecar = {"ptr": ptr, "sha_orig": hashlib.sha256(text.encode()).hexdigest()}  # restricted, local only
    return record, red, sidecar
