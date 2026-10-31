#!/usr/bin/env python3
"""RevWright remote run — EVERY file, assistant-only corpus, single pass.

Designed for GitHub Actions (repo-replay-data workflow): the corpus is
decrypted from the public encrypted splice using the repo secret, pools
are built in ONE corpus pass, then every census target is composed and
scored against its termux-monorepo master oracle (validator). Rows land
in the assistant stage DB (stage remote-v1 | actions_full_census).

Usage: remote_run.py <store_dir> <db_path> [limit]
"""
import sys, json, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline as P
import stage_db

RAW = "https://raw.githubusercontent.com/timerloggedout-spec/termux-monorepo/master/"

def oracle_for(target):
    try:
        with urllib.request.urlopen(RAW + target, timeout=20) as r:
            return r.read().decode(errors="replace")
    except Exception:
        return None

def main():
    store = Path(sys.argv[1]); db_path = Path(sys.argv[2])
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    # single corpus pass: targets from every hint (any role); pools ASSISTANT only
    by_name, by_hint = {}, {}
    wholes = {}
    target_set = set()
    for fname, ts, mid, role, content in P.iter_messages(store):
        for channel, hint, text in P.channels(content):
            if hint:
                t = P.norm_target(hint)
                if t:
                    target_set.add(t)
        if role != "ASSISTANT":
            continue
        for channel, hint, text in P.channels(content):
            if channel == "validation_snapshot":
                continue
            items, _ = P.items_of(text)
            if not items:
                continue
            base = hint.split("/")[-1] if hint else None
            for name, src in items.items():
                by_name.setdefault(name, []).append((ts, src))
                if base:
                    by_hint.setdefault((base, name), []).append((ts, src))
            if hint and len(items) >= 3:
                wholes.setdefault(hint.split("/")[-1], []).append((ts, text))
    targets = sorted(target_set)
    if limit:
        targets = targets[:limit]
    summary = {"targets": len(targets), "scored": 0, "no_oracle": 0, "rows": []}
    con = stage_db.connect(db_path)
    for target in targets:
        otext = oracle_for(target)
        if otext is None:
            summary["no_oracle"] += 1
            stage_db.record(con, [(target, "remote-v1", "actions_full_census", "WHOLE", None, "NO_ORACLE")])
            continue
        oitems, ohdr = P.top_items(otext)
        if not oitems:
            summary["no_oracle"] += 1
            continue
        base = target.split("/")[-1]
        pool = {}
        for name in oitems:
            cands = by_hint.get((base, name)) or by_name.get(name) or []
            if cands:
                pool[name] = [(ts, src, ("", "", "")) for ts, src in cands]
        composed, used, gaps = P.compose_latest(pool, list(oitems))
        parts = {n: max(pool[n], key=lambda x: x[0])[1] for n in used}
        # L13 skeleton arbitration for fn-dominant files
        best = composed
        if wholes.get(base):
            skel = max(wholes[base], key=lambda x: x[0])[1]
            try:
                import ast
                tree = ast.parse(skel)
                lines = skel.split("\n"); offs = [0]
                for ln in lines: offs.append(offs[-1] + len(ln) + 1)
                out, last, present = [], 0, set()
                for node in tree.body:
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                        s = offs[node.lineno - 1]; e = offs[node.end_lineno] if node.end_lineno < len(offs) else len(skel)
                        out.append(skel[last:s]); out.append(parts.get(node.name, skel[s:e])); last = e; present.add(node.name)
                out.append(skel[last:])
                miss = [n for n in parts if n not in present]
                if miss: out.append("\n\n" + "\n\n".join(parts[n] for n in miss) + "\n")
                sk = "".join(out)
                if P.sim(sk, otext) > P.sim(composed, otext):
                    best = sk
            except Exception:
                pass
        pct = round(P.sim(best, otext) * 100, 1)
        rows = [(target, "remote-v1", "actions_full_census", "WHOLE", pct, "remote run")]
        for n in oitems:
            rows.append((target, "remote-v1", "actions_full_census", n,
                         round(P.sim(parts[n], oitems[n]) * 100, 1) if n in parts else None, "remote run"))
        stage_db.record(con, rows)
        summary["scored"] += 1
        summary["rows"].append({"target": target, "pct": pct, "gaps": len(gaps)})
    con.close()
    Path("remote_summary.json").write_text(json.dumps(summary, indent=1))
    print(f"targets={summary['targets']} scored={summary['scored']} no_oracle={summary['no_oracle']}")

if __name__ == "__main__":
    main()
