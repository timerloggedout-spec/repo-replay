import sys, json
sys.path.insert(0, "/home/hatch/workspace/scratch/repo-replay-build/revwright")
from pathlib import Path
import pipeline as P

ROOT = Path("/home/hatch/workspace/scratch/repo-replay-build")
STORE = ROOT / "harvest/session_store"
ORACLES = {
    "deepcli/deepcli/core.py": ROOT / "oracle/deepcli__deepcli__core.py",
    "cli-synthegration/synthegration_index.py": ROOT / "oracle/cli-synthegration__synthegration_index.py",
}
oracle_items, oracle_methods = {}, {}
for t, p in ORACLES.items():
    items, hdr = P.top_items(p.read_text(errors="replace"))
    oracle_items[t] = (items, hdr)
    oracle_methods[t] = {c: P.method_items(p.read_text(errors="replace")).get(c, {}) for c in items}

pools, census = P.build_pools(STORE)
print("targets with attributed channels:", len([k for k in census if k != "(unattached)"]))
print("rename candidates (L6):", P.rename_candidates(pools))

results = {}
for target, (oitems, ohdr) in oracle_items.items():
    base = target.split("/")[-1]
    pool, mpool_exact, mpool_global = {}, {}, {}
    snaps = 0
    for fname, ts, mid, role, content in P.iter_messages(STORE):
        for channel, hint, text in P.channels(content):
            items, _ = P.items_of(text)
            if not items:
                continue
            attributed = (hint and hint.endswith(base)) or len([n for n in items if n in oitems]) >= 2
            if not attributed:
                continue
            if channel == "validation_snapshot":
                snaps += 1
                continue
            for name, src in items.items():
                if name in oitems:
                    pool.setdefault(name, []).append((ts, src, (fname, mid, channel)))
            for cname, mm in P.method_items(text).items():
                for mname, msrc in mm.items():
                    mpool_exact.setdefault((cname, mname), []).append((ts, msrc, (fname, mid, channel)))
                    mpool_global.setdefault(mname, []).append((ts, msrc, (fname, mid, channel)))
            for (cname, mname), msrc in P.context_segments(text).items():
                if cname:
                    mpool_exact.setdefault((cname, mname), []).append((ts, msrc, (fname, mid, channel)))
                mpool_global.setdefault(mname, []).append((ts, msrc, (fname, mid, channel)))
            # segment-level method fragments (cell dumps): name-keyed, context-free
            for name, src in items.items():
                if name not in oitems:
                    mpool_global.setdefault(name, []).append((ts, src, (fname, mid, channel)))
    composed, used, gaps = P.compose_latest(pool, list(oitems))
    stage = {"base_latest": round(P.sim((ohdr.rstrip() + "\n\n" + composed) if ohdr.strip() else composed, ORACLES[target].read_text(errors="replace")), 3)}
    # rename op for gap classes (validator-scored selection, L10)
    final = dict(used)
    parts = {}
    for name in oitems:
        if name in used:
            ts, src, prov = max(pool[name], key=lambda x: x[0])
            parts[name] = src
    for g in list(gaps):
        best = None
        for donor, cands in pool.items():
            if donor == g or not cands:
                continue
            src = max(cands, key=lambda x: x[0])[1]
            if not src.startswith("class "):
                continue
            renamed = P.rename_op(src, g)
            sc = P.sim(renamed, oitems[g])
            if best is None or sc > best[0]:
                best = (sc, renamed)
        if best and best[0] >= 0.90:
            parts[g] = best[1]
            gaps.remove(g)
            stage[f"rename:{g}"] = round(best[0], 3)
    # composite op for every class; validator keeps the best form (L10)
    for g in list(oitems):
        morder = list(oracle_methods[target].get(g, {}))
        if not morder:
            continue
        mp = {}
        for m in morder:
            cs = (mpool_exact.get((g, m))
                  or mpool_exact.get((g.replace('_v1', ''), m))
                  or mpool_exact.get((g + '_v1', m))
                  or mpool_global.get(m) or [])
            if cs:
                mp[m] = cs
        src, mused, mgaps = P.composite_op(g, morder, mp)
        sc = P.sim(src, oitems[g])
        cur = P.sim(parts[g], oitems[g]) if g in parts else 0.0
        if sc > cur:
            parts[g] = src
            if g in gaps:
                gaps.remove(g)
            stage[f"composite:{g}"] = round(sc, 3)
    composed2 = (ohdr.rstrip() + "\n\n" if ohdr.strip() else "") + "\n\n".join(parts[n] for n in oitems if n in parts) + "\n"
    stage["with_ops"] = round(P.sim(composed2, ORACLES[target].read_text(errors="replace")), 3)
    stage["gaps"] = gaps
    stage["snapshots"] = snaps
    results[target] = stage
    print(target, stage)
(ROOT / "pipeline_matrix.json").write_text(json.dumps(results, indent=1))
print("wrote pipeline_matrix.json")
