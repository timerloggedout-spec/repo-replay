#!/usr/bin/env python3
"""RevWright compose v0.2 — chain ∘ order ⇒ file.
Snapshot rule: a block whose length ≥ 50% of the chain's max block length is
snapshot-like; the composed file = the LAST snapshot-like block in chain
order, with later fragments spliced when their first line anchors uniquely
in the base. Fragments before the last snapshot are history (the DAG keeps
them; composition consumes the chain, not just the tail).
"""
import difflib

def compose(versions):
    """versions: [(ts, msg, role, code)] in chain order → (text, stats)"""
    if not versions: return "", {"snapshots": 0, "spliced": 0}
    maxlen = max(len(v[3]) for v in versions)
    snaps = [v for v in versions if len(v[3]) >= 0.5 * maxlen]
    base_idx = versions.index(snaps[-1])
    text = snaps[-1][3]
    spliced = 0
    for ts, msg, role, code in versions[base_idx + 1:]:
        lines = code.split("\n")
        anchor = next((l for l in lines if l.strip()), None)
        if anchor and text.count(anchor) == 1:
            start = text.index(anchor)
            end = start + len(code) if text[start:start + len(code)] else start
            text = text[:start] + code + text[start + len(anchor):].split("\n", 1)[-1].join(["\n", ""]) if False else text[:start] + code + text[start + len(anchor):]
            spliced += 1
    return text, {"snapshots": len(snaps), "spliced": spliced, "versions": len(versions)}

def sim(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()
