#!/usr/bin/env python3
"""RevWright extract v0.1 — dual-key join (HARVEST-001 derived).
conv_repo objects (hash-only DAG) ⋈ session_store exports:
  key1 content_hash = sha256(text)[:16]   (primary)
  key2 (session, message_id)              (fallback; conv e102 hashes are all
                                           sha256('') = GAP, never a resolution)
Emits redacted transcripts + index + sidecar through the sensitivity gate.
"""
import hashlib, json, sys
from pathlib import Path
import sensitivity

EMPTY = "e3b0c44298fc1c14"  # sha256('')[:16]

def h16(b: bytes) -> str: return hashlib.sha256(b).hexdigest()[:16]

def load_store_texts(store_dir: Path):
    """(hash → text) ∧ ((file_stem, msg_id) → text) from session_store exports."""
    by_hash, by_msg = {}, {}
    for f in sorted(store_dir.glob("*.json")):
        try: data = json.loads(f.read_text(errors="replace"))
        except Exception: continue
        entries = data if isinstance(data, list) else [data]
        for e in entries:
            if isinstance(e, dict) and isinstance(e.get("content"), str):
                by_hash.setdefault(h16(e["content"].encode()), e["content"])
                if e.get("message_id") is not None:
                    by_msg[(f.stem, str(e["message_id"]))] = e["content"]
            def walk(v):
                if isinstance(v, str): by_hash.setdefault(h16(v.encode()), v)
                elif isinstance(v, dict):
                    for vv in v.values(): walk(vv)
                elif isinstance(v, list):
                    for vv in v: walk(vv)
            walk(e)
        # title-named exports: session stem = suffix after last '_'
        if "_" in f.stem:
            sid = f.stem.rsplit("_", 1)[-1]
            for e in entries:
                if isinstance(e, dict) and isinstance(e.get("content"), str) and e.get("message_id") is not None:
                    by_msg.setdefault((sid, str(e["message_id"])), e["content"])
    return by_hash, by_msg

def run(conv_dir: Path, store_dir: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    by_hash, by_msg = load_store_texts(store_dir)
    records, sidecars, stats = [], [], {"hash": 0, "msgid": 0, "gap": 0, "quarantined": 0}
    for sdir in sorted((conv_dir / "sessions").iterdir()):
        sid = sdir.name
        for op in sorted((sdir / "objects").glob("*.json")):
            o = json.loads(op.read_text())
            ch, mid = o["content_hash"], str(o["message_id"])
            text, via = None, None
            if ch != EMPTY and ch in by_hash: text, via = by_hash[ch], "hash"
            elif (sid[:8], mid) in by_msg or (sid, mid) in by_msg:
                text, via = by_msg.get((sid[:8], mid)) or by_msg.get((sid, mid)), "msgid"
            if text is None:
                stats["gap"] += 1
                records.append({"ptr": f"{sid}:{mid}", "status": "GAP",
                                "reason": "empty_hash" if ch == EMPTY else "unresolved"})
                continue
            stats[via] += 1
            rec, red, side = sensitivity.process(f"{sid}:{mid}", text)
            rec["via"] = via
            if rec["quarantined"]: stats["quarantined"] += 1
            records.append(rec); sidecars.append(side)
            (out / f"{sid[:8]}-{mid}.redacted.txt").write_text(red)
    (out / "index.json").write_text(json.dumps(records, indent=1))
    (out / "sensitivity-sidecar.json").write_text(json.dumps(sidecars, indent=1))  # RESTRICTED local
    print(json.dumps(stats))

if __name__ == "__main__":
    base = Path(sys.argv[1])
    run(base / "conv_repo", base / "session_store", Path(sys.argv[2]))
