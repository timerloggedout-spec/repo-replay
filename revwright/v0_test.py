import sys, json, subprocess, shutil
sys.path.insert(0, "/home/hatch/workspace/scratch/repo-replay-build/revwright")
from pathlib import Path
import pipeline as P

ROOT = Path("/home/hatch/workspace/scratch/repo-replay-build")
TEST = ROOT / "v0-test"
STORE = ROOT / "harvest/session_store"
FILES = {
    "deepcli/deepcli/core.py": ROOT / "oracle/deepcli__deepcli__core.py",
    "cli-synthegration/synthegration_index.py": ROOT / "oracle/cli-synthegration__synthegration_index.py",
}
def sh(*a, cwd):
    return subprocess.run(a, cwd=cwd, capture_output=True, text=True)

if TEST.exists():
    shutil.rmtree(TEST)
for rel, src in FILES.items():
    dst = TEST / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(errors="replace"))
sh("git", "init", "-q", cwd=TEST)
sh("git", "config", "user.email", "v0@repo-replay.test", cwd=TEST)
sh("git", "config", "user.name", "V0 Oracle", cwd=TEST)
sh("git", "add", "-A", cwd=TEST)
c = sh("git", "commit", "-qm", "V0 oracle tree", cwd=TEST)
head = sh("git", "rev-parse", "HEAD", cwd=TEST).stdout.strip()
print("V0 oracle committed:", head[:12])

# deletion event (the gap-fill case): both files removed from the worktree
for rel in FILES:
    (TEST / rel).unlink()
print("deleted from worktree:", list(FILES))

# replay: reconstruct from session provenance only (pipeline pools + ops)
results = {}
for target, oracle_path in FILES.items():
    otext = oracle_path.read_text(errors="replace")
    oitems, ohdr = P.top_items(otext)
    omethods = P.method_items(otext)
    base = target.split("/")[-1]
    pool, mpool_exact, mpool_global = {}, {}, {}
    for fname, ts, mid, role, content in P.iter_messages(STORE):
        for channel, hint, text in P.channels(content):
            items, _ = P.items_of(text)
            if not items:
                continue
            if not ((hint and hint.endswith(base)) or len([n for n in items if n in oitems]) >= 2):
                continue
            if channel == "validation_snapshot":
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
    for g in list(oitems):
        morder = list(omethods.get(g, {}))
        if not morder:
            continue
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
    rebuilt = (ohdr.rstrip() + "\n\n" if ohdr.strip() else "") + "\n\n".join(parts[n] for n in oitems if n in parts) + "\n"
    (TEST / target).write_text(rebuilt)
    results[target] = {"sim_vs_git_head": round(P.sim(rebuilt, otext), 3), "gaps": gaps}
    print(target, results[target])

st = sh("git", "status", "--porcelain", cwd=TEST).stdout
diffstat = sh("git", "diff", "--stat", cwd=TEST).stdout.strip()
fsck = sh("git", "fsck", "--strict", cwd=TEST)
print("git status after replay:\n" + (st or "(clean)"))
print("git diff --stat:\n" + diffstat)
print("fsck rc:", fsck.returncode, fsck.stdout.strip()[:120], fsck.stderr.strip()[:120])
(ROOT / "v0_results.json").write_text(json.dumps(results, indent=1))
