import sys, ast, json
sys.path.insert(0, "/home/hatch/workspace/scratch/repo-replay-build")
sys.path.insert(0, "/home/hatch/workspace/scratch/repo-replay-build/revwright")
import pipeline as P
import stage_db
from role_split_run import ORACLES, STORE
from pathlib import Path

def spans_of(text):
    """Yield (kind, name, start, end) char spans for top-level items."""
    try:
        tree = ast.parse(text)
    except Exception:
        return []
    lines = text.split("\n")
    offs = [0]
    for ln in lines:
        offs.append(offs[-1] + len(ln) + 1)
    out = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            s = offs[node.lineno - 1]
            e = offs[node.end_lineno] if node.end_lineno < len(offs) else len(text)
            out.append((node.name, s, e))
    return out

def build(target, oracle_path):
    otext = oracle_path.read_text(errors="replace")
    oitems, ohdr = P.top_items(otext)
    base = target.split("/")[-1]
    pool, wholes = {}, []
    for fname, ts, mid, role, content in P.iter_messages(STORE):
        if role != "ASSISTANT":
            continue
        for channel, hint, text in P.channels(content):
            if channel == "validation_snapshot":
                continue
            items, _ = P.items_of(text)
            if not items:
                continue
            known = [n for n in items if n in oitems]
            if not ((hint and hint.endswith(base)) or len(known) >= 1):
                continue
            for name, src in items.items():
                if name in oitems:
                    pool.setdefault(name, []).append((ts, src))
            if len(known) >= max(3, len(oitems) // 2):
                wholes.append((ts, text))
    parts = {n: max(c, key=lambda x: x[0])[1] for n, c in pool.items() if c}
    return otext, oitems, parts, wholes

def skeleton_compose(skel, parts):
    sp = spans_of(skel)
    if not sp:
        return skel
    out, last = [], 0
    for name, s, e in sp:
        out.append(skel[last:s])
        out.append(parts.get(name, skel[s:e]))
        last = e
    out.append(skel[last:])
    present = {n for n, _, _ in sp}
    missing = [n for n in parts if n not in present]
    if missing:  # v0.8b: items with no skeleton span are appended, not lost
        out.append("\n\n" + "\n\n".join(parts[n] for n in missing) + "\n")
    return "".join(out)

db = stage_db.db_for("assistant")
results = {}
for target, opath in ORACLES.items():
    otext, oitems, parts, wholes = build(target, opath)
    row = {}
    if wholes:
        latest_skel = max(wholes, key=lambda x: x[0])[1]
        blind = skeleton_compose(latest_skel, parts)
        row["blind_latest_skeleton"] = round(P.sim(blind, otext) * 100, 1)
        best_ts, best_skel, best_sc = None, None, -1
        for ts, t in wholes:
            sc = P.sim(skeleton_compose(t, parts), otext)
            if sc > best_sc:
                best_sc, best_skel, best_ts = sc, t, ts
        row["validator_best_skeleton"] = round(best_sc * 100, 1)
        row["skeleton_candidates"] = len(wholes)
        stage_db.record_run(target, "pipeline-v0.8b", "skeleton_blind", row["blind_latest_skeleton"],
                            source="ASSISTANT-FOCUS v0.8b skeleton (latest, missing appended)", db_path=db)
        stage_db.record_run(target, "pipeline-v0.8b", "skeleton_validator", row["validator_best_skeleton"],
                            source="ASSISTANT-FOCUS v0.8b skeleton (validator-picked, missing appended)", db_path=db)
    results[target] = row
    print(target, row)
json.dump(results, open("/home/hatch/workspace/scratch/repo-replay-build/skeleton_matrix.json", "w"), indent=1)
