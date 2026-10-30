import sys, json, hashlib
sys.path.insert(0, "/home/hatch/workspace/scratch/repo-replay-build/revwright")
from pathlib import Path
import pipeline as P
import stage_db

ROOT = Path("/home/hatch/workspace/scratch/repo-replay-build")
STORE = ROOT / "harvest/session_store"
ORACLES = {
    "deepcli/deepcli/core.py": ROOT / "oracle/deepcli__deepcli__core.py",
    "cli-synthegration/synthegration_index.py": ROOT / "oracle/cli-synthegration__synthegration_index.py",
}
CORPORA = {"assistant": {"ASSISTANT"}, "user": {"USER"}, "combined": None}

def compose_for_target(target, oracle_path, roles, attn_min=2):
    otext = oracle_path.read_text(errors="replace")
    oitems, ohdr = P.top_items(otext)
    omethods = P.method_items(otext)
    base = target.split("/")[-1]
    pool, mpool_exact, mpool_global, index_rows = {}, {}, {}, []
    def h(src): return hashlib.sha256(src.encode()).hexdigest()[:16]
    for fname, ts, mid, role, content in P.iter_messages(STORE):
        if roles is not None and role not in roles:
            continue
        for channel, hint, text in P.channels(content):
            items, _ = P.items_of(text)
            if not items:
                continue
            if not ((hint and hint.endswith(base)) or len([n for n in items if n in oitems]) >= attn_min):
                continue
            if channel == "validation_snapshot":
                continue
            kinds = {}
            try:
                import ast as _ast
                tree = _ast.parse(text)
                for node in tree.body:
                    if isinstance(node, _ast.ClassDef): kinds[node.name] = "class"
                    elif isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)): kinds[node.name] = "fn"
            except Exception:
                pass
            for name, src in items.items():
                if name in oitems:
                    pool.setdefault(name, []).append((ts, src, (fname, mid, channel)))
                    index_rows.append((h(src), kinds.get(name, "fn"), name, None, target, fname, mid, channel))
            for cname, mm in P.method_items(text).items():
                for mname, msrc in mm.items():
                    mpool_exact.setdefault((cname, mname), []).append((ts, msrc, (fname, mid, channel)))
                    mpool_global.setdefault(mname, []).append((ts, msrc, (fname, mid, channel)))
            for (cname, mname), msrc in P.context_segments(text).items():
                if cname:
                    mpool_exact.setdefault((cname, mname), []).append((ts, msrc, (fname, mid, channel)))
                    index_rows.append((h(msrc), "method", mname, cname, target, fname, mid, channel))
                mpool_global.setdefault(mname, []).append((ts, msrc, (fname, mid, channel)))
    composed, used, gaps = P.compose_latest(pool, list(oitems))
    parts = {}
    for name in oitems:
        if name in used:
            parts[name] = max(pool[name], key=lambda x: x[0])[1]
    for g in list(gaps):
        best = None
        for donor, cands in pool.items():
            if donor == g or not cands:
                continue
            src = max(cands, key=lambda x: x[0])[1]
            if src.startswith("class "):
                sc = P.sim(P.rename_op(src, g), oitems[g])
                if best is None or sc > best[0]:
                    best = (sc, P.rename_op(src, g))
        if best and best[0] >= 0.90:
            parts[g] = best[1]; gaps.remove(g)
    per_item = {}
    for g in list(oitems):
        morder = list(omethods.get(g, {}))
        if morder:
            mp = {}
            for m in morder:
                cs = (mpool_exact.get((g, m)) or mpool_exact.get((g.replace('_v1', ''), m))
                      or mpool_exact.get((g + '_v1', m)) or mpool_global.get(m) or [])
                if cs:
                    mp[m] = cs
            src, _, _ = P.composite_op(g, morder, mp)
            if P.sim(src, oitems[g]) > (P.sim(parts[g], oitems[g]) if g in parts else 0.0):
                parts[g] = src
                if g in gaps:
                    gaps.remove(g)
        if g in parts:
            per_item[g] = round(P.sim(parts[g], oitems[g]) * 100, 1)
    rebuilt = (ohdr.rstrip() + "\n\n" if ohdr.strip() else "") + "\n\n".join(parts[n] for n in oitems if n in parts) + "\n"
    return round(P.sim(rebuilt, otext) * 100, 1), per_item, gaps, index_rows

results = {}
for corpus, roles in CORPORA.items():
    db = stage_db.db_for(corpus)
    for target, opath in ORACLES.items():
        whole, per_item, gaps, idx = compose_for_target(target, opath, roles)
        stage_db.record_run(target, "pipeline-v0.6", "role_split_auto", whole,
                            per_item=per_item, source="ROLE-SPLIT experiment", db_path=db)
        stage_db.record_index(idx, db_path=db)
        results[f"{corpus}:{target}"] = {"whole": whole, "gaps": gaps, "index_rows": len(idx)}
        print(corpus, target, "whole%", whole, "gaps", gaps, "index rows", len(idx))
(ROOT / "role_split_matrix.json").write_text(json.dumps(results, indent=1))
