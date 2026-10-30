#!/usr/bin/env python3
"""RevWright extract v0 — session exports -> objects + forward/reverse index + signal.
Stdlib only. Resumable: checkpoint.json in out dir; re-runs skip done files.
Provider-agnostic: walks .json/.md/.txt; fenced code blocks become objects;
cmd-output blocks (tree/ls/search/alias/PATH) become signal records, never objects.
"""
import json, hashlib, re, sys
from pathlib import Path

FENCE = re.compile(r"```(\w*)\n(.*?)```", re.S)
CMD = re.compile(r"(^\s*(ls\s+-\w+|tree\b|find\s|grep\s|rg\s|alias\b|export\s+PATH|echo\s+\$PATH|which\s))|(\$\s*(ls|tree|find|grep|cd|cat)\b)", re.M)
EXCL = re.compile(r"(\.gitignore|excluded|skip|ignore)", re.I)

def h16(b: bytes) -> str: return hashlib.sha256(b).hexdigest()[:16]

def extract_file(path: Path, session_id: str):
    text = path.read_text(errors="replace")
    objs, signals = [], []
    for i, m in enumerate(FENCE.finditer(text)):
        lang, code = m.group(1), m.group(2)
        if CMD.search(code) or (not lang and CMD.search(code)):
            kind = "exclusion" if EXCL.search(code) else ("layout" if re.search(r"\bls\b|\btree\b", code) else "search" if re.search(r"grep|rg|find", code) else "env")
            signals.append({"class": kind, "session": session_id, "blk": i, "hash": h16(code.encode())})
            continue
        if len(code.strip()) < 2: continue
        objs.append({"hash": h16(code.encode()), "session": session_id, "blk": i, "lang": lang or None, "bytes": len(code.encode())})
    # unfenced signal: lines that are pure cmd output headers
    return objs, signals

def main(src: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    ckpt_f = out / "checkpoint.json"
    ckpt = json.loads(ckpt_f.read_text()) if ckpt_f.exists() else {"done": []}
    objects, fwd, rev, signals = {}, {}, {}, []
    idx_f = out / "index.json"
    if idx_f.exists():
        prev = json.loads(idx_f.read_text()); objects = prev["objects"]; fwd = prev["forward"]; rev = prev["reverse"]; signals = prev["signals"]
    files = sorted(p for p in src.rglob("*") if p.suffix in {".json", ".md", ".txt"} and p.is_file())
    for p in files:
        key = str(p.relative_to(src))
        if key in ckpt["done"]: continue
        try: objs_f, sig_f = extract_file(p, session_id=key)
        except Exception: continue
        for o in objs_f:
            objects[o["hash"]] = o
            ptr = f'{o["session"]}:{o["blk"]}'
            fwd[ptr] = o["hash"]
            rev.setdefault(o["hash"], []).append(ptr)
        signals.extend(sig_f)
        ckpt["done"].append(key)
        ckpt_f.write_text(json.dumps(ckpt))  # checkpoint per file = resumable
    idx_f.write_text(json.dumps({"objects": objects, "forward": fwd, "reverse": rev, "signals": signals}, indent=1))
    print(f"files={len(ckpt['done'])} objects={len(objects)} forward={len(fwd)} reverse={len(rev)} signals={len(signals)}")

if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
