#!/usr/bin/env python3
"""RevWright remote run v5 — EVERY file, assistant-only corpus, single pass.

v5 (manager-ruled lever b): session-evidence is measured BEFORE the
oracle fetch — every target first gets a basename-level session state
(hint-attributed items or whole-file snapshots in the assistant corpus),
so gap rows (FETCH_FAIL / NO_ORACLE) carry session=present|absent and
the absent class is unmasked for L7 gap-cause classification.
v6 (manager-ruled lever a): the V2 snapshot pack carries ALL GitLab
branches (tree/<branch>/<path>); indexing strips the branch component,
prefers master on key conflicts, records the branch per oracle
(v2_snapshot@<branch>:<sha256[:16]>). Legacy flat packs still index.
v7: pack v3 is a git-objects pack (the shallow .git store itself; the
242-branch full-tree shape failed on scale) — when v2_dir is a git repo,
index via git ls-tree per branch ref (master preferred) and read blobs
on demand via git show. Filesystem packs (v6/v1) unchanged.
v8: whole-file fallback. NO_ORACLE splits into oracle_miss (resolved
path fetched nothing — gitlinks et al.) vs the no-items class (oracle
present, zero top-level items: md/sh/dotfiles/all-top-level py). The
no-items class is now SCORED whole-file: assistant raw hint texts are
pooled per basename (validation snapshots excluded, L2) and the latest
is similarity-scored against the oracle (validator arbitrates across
oracle candidates). Session-evidence instrument widens to raw presence.
v9: gap-fill export. Absent-class targets WITH session content (149 at
v8) are RECONSTRUCTED into gapfill_dir (argv[6]): latest whole snapshot
> latest raw text > item-compose of hint-attributed items; MANIFEST.json
records {target, method, bytes, sha256, versions} per file. Unscored by
design — no oracle exists for this class anywhere.
v10: L14 path-exact before basename. Recon proved basename collision in
the whole-file pool (README.md x6 targets, TASK_QUEUE.md x5, taDone.md
x6 sharing one latest-text): raw texts are now ALSO pooled by full hint
path; whole scoring prefers the target's own path texts (whole_path)
over the basename pool (whole_base). Dual arbitration (L13 extended):
when an item-compose variant exists AND path-exact raw text exists, the
whole-path score competes; the better method wins the WHOLE row, the
loser is noted in the source string. Gapfill prefers raw_path too.

GitHub Actions (repo-replay-data): corpus decrypted from the public
encrypted splice via repo secret; pools built in ONE pass; every census
target composed + scored vs validators: V1 = termux-monorepo master
(exact -> unique basename -> AMBIGUOUS arbitration by validator best-of),
V2 = GitLab earlier copy for the absent class. Fetch splits 404
(NO_ORACLE) from transient (FETCH_FAIL, retry x2). Rows -> assistant
stage DB (remote-v10 | actions_full_census).

Usage: remote_run.py <store_dir> <db_path> [limit] [tree_file] [v2_dir]
v2_dir = local GitLab snapshot clone (tree+blob pack); absent-class
oracle read from disk, sha256 recorded (hash-verified fill_gap source).
"""
import sys, json, ast, time, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline as P
import stage_db

RAW = "https://raw.githubusercontent.com/timerloggedout-spec/termux-monorepo/master/"
GITLAB_RAW = "https://gitlab.com/a-group2180532/termux-monorepo/-/raw/main/"

class FetchFail(Exception):
    pass

def fetch(url):
    for attempt in range(2):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                return r.read().decode(errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt == 1:
                raise FetchFail(str(e.code))
        except Exception as e:
            if attempt == 1:
                raise FetchFail(type(e).__name__)
        time.sleep(2)

def load_tree(path_arg):
    if path_arg and Path(path_arg).exists():
        return [l.strip() for l in Path(path_arg).read_text().splitlines() if l.strip()]
    return []

def resolve(target, tree_set, by_base):
    if target in tree_set:
        return target, "exact", [target]
    cands = by_base.get(target.split("/")[-1], [])
    if len(cands) == 1:
        return cands[0], "basename_unique", cands
    if cands:
        return None, "ambiguous", cands[:4]
    return None, "absent", []

def compose_for(oitems, ohdr, pool, wholes_base):
    composed, used, gaps = P.compose_latest(pool, list(oitems))
    parts = {n: max(pool[n], key=lambda x: x[0])[1] for n in used}
    best = composed
    if wholes_base:
        skel = max(wholes_base, key=lambda x: x[0])[1]
        try:
            tree = ast.parse(skel)
            lines = skel.split("\n"); offs = [0]
            for ln in lines: offs.append(offs[-1] + len(ln) + 1)
            out, last, present = [], 0, set()
            for node in tree.body:
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    s = offs[node.lineno - 1]
                    e = offs[node.end_lineno] if node.end_lineno < len(offs) else len(skel)
                    out.append(skel[last:s]); out.append(parts.get(node.name, skel[s:e]))
                    last = e; present.add(node.name)
            out.append(skel[last:])
            miss = [n for n in parts if n not in present]
            if miss: out.append("\n\n" + "\n\n".join(parts[n] for n in miss) + "\n")
            sk = "".join(out)
            if P.sim(sk, compose_for.oracle_text) > P.sim(composed, compose_for.oracle_text):
                best = sk
        except Exception:
            pass
    return best, parts, gaps

def main():
    store = Path(sys.argv[1]); db_path = Path(sys.argv[2])
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    tree = load_tree(sys.argv[4] if len(sys.argv) > 4 else None)
    v2_dir = Path(sys.argv[5]) if len(sys.argv) > 5 else None
    gapfill_dir = Path(sys.argv[6]) if len(sys.argv) > 6 else None
    gapfill_rows = []
    v2_files = {}
    v2_git = None
    if v2_dir and (v2_dir / ".git").exists():
        import subprocess
        v2_git = str(v2_dir)
        def gitout(*args):
            r = subprocess.run(["git", "-c", "safe.directory=*", "-C", v2_git, *args], capture_output=True)
            return r.stdout.decode(errors="replace")
        refs = [l for l in gitout("for-each-ref", "--format=%(refname)", "refs/remotes/gitlab").splitlines() if l]
        entries = []
        for ref in refs:
            br = ref[len("refs/remotes/gitlab/"):]
            for p in gitout("ls-tree", "-r", "--name-only", ref).splitlines():
                if p:
                    entries.append((br, p))
        entries.sort(key=lambda e: (e[0] != "master", e[0]))
        for br, p in entries:
            v2_files.setdefault(p, (f"git:{br}", br))
        print(f"v2 snapshot (git-objects): {len(v2_files)} files across {len(refs)} branches")
    elif v2_dir and v2_dir.exists():
        branch_mode = (v2_dir / "master").is_dir()
        entries = []
        for fp in v2_dir.rglob("*"):
            if fp.is_file() and ".git" not in fp.parts:
                rel = fp.relative_to(v2_dir)
                if branch_mode and len(rel.parts) > 1:
                    entries.append((rel.parts[0], str(Path(*rel.parts[1:])), fp))
                else:
                    entries.append(("root", str(rel), fp))
        entries.sort(key=lambda e: (e[0] != "master", e[0]))
        for br, key, fp in entries:
            v2_files.setdefault(key, (fp, br))
        print(f"v2 snapshot: {len(v2_files)} files (branch_mode={branch_mode})")
    tree_set = set(tree)
    by_base = {}
    for tp in tree:
        by_base.setdefault(tp.split("/")[-1], []).append(tp)
    by_name, by_hint, wholes, raw, raw_path = {}, {}, {}, {}, {}
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
            if hint:
                raw.setdefault(hint.split("/")[-1], []).append((ts, text))
                raw_path.setdefault(hint, []).append((ts, text))
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
    summary = {"targets": len(targets), "scored": 0, "no_oracle": 0, "fetch_fail": 0, "rows": [], "gap_session": {"present": 0, "absent": 0}, "whole_scored": 0}
    con = stage_db.connect(db_path)
    for target in targets:
        resolved, how, cands = resolve(target, tree_set, by_base)
        base0 = target.split("/")[-1]
        ev_items = {n for (b, n) in by_hint if b == base0}
        session_state = "present" if (ev_items or wholes.get(base0) or raw.get(base0) or raw_path.get(target)) else "absent"
        oracle_texts = []
        try:
            if resolved is not None:
                t = fetch(RAW + resolved)
                if t is not None:
                    oracle_texts = [(resolved, t, "v1")]
            elif how == "ambiguous":
                for cand in cands:
                    t = fetch(RAW + cand)
                    if t is not None:
                        oracle_texts.append((cand, t, "v1"))
            elif how == "absent":
                import hashlib
                cand = None
                if target in v2_files:
                    cand = target
                else:
                    same = [r for r in v2_files if r.split("/")[-1] == target.split("/")[-1]]
                    if len(same) == 1:
                        cand = same[0]
                if cand is not None:
                    loc, br = v2_files[cand]
                    if v2_git:
                        import subprocess
                        rr = subprocess.run(["git", "-c", "safe.directory=*", "-C", v2_git, "show", f"refs/remotes/gitlab/{br}:{cand}"], capture_output=True)
                        t = rr.stdout.decode(errors="replace")
                    else:
                        t = loc.read_text(errors="replace")
                    h = hashlib.sha256(t.encode()).hexdigest()[:16]
                    oracle_texts = [(cand, t, f"v2_snapshot@{br}:{h}")]
                    how = "v2_snapshot"
                else:
                    t = fetch(GITLAB_RAW + target)
                    if t is not None:
                        oracle_texts = [(target, t, "v2")]
                        how = "v2_gitlab"
        except FetchFail:
            summary["fetch_fail"] += 1
            summary["gap_session"][session_state] += 1
            stage_db.record(con, [(target, "remote-v10", "actions_full_census", "WHOLE", None, f"FETCH_FAIL:{how}:session={session_state}")])
            summary["rows"].append({"target": target, "how": how, "gap": "FETCH_FAIL", "session": session_state})
            if gapfill_dir is not None and how == "absent" and session_state == "present":
                import hashlib as _hl
                text, method, nver = None, None, 0
                if raw_path.get(target):
                    text = max(raw_path[target], key=lambda x: x[0])[1]
                    method, nver = "raw_path_latest", len(raw_path[target])
                elif wholes.get(base0):
                    text = max(wholes[base0], key=lambda x: x[0])[1]
                    method, nver = "whole_snapshot", len(wholes[base0])
                elif raw.get(base0):
                    text = max(raw[base0], key=lambda x: x[0])[1]
                    method, nver = "raw_latest", len(raw[base0])
                elif ev_items:
                    pool = {}
                    for n2 in ev_items:
                        cs = by_hint.get((base0, n2)) or []
                        if cs:
                            pool[n2] = [(ts2, s2, ("", "", "")) for ts2, s2 in cs]
                    text, _u, _g = P.compose_latest(pool, sorted(ev_items))
                    method, nver = "item_compose", len(ev_items)
                if text:
                    out = gapfill_dir / target
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(text)
                    gapfill_rows.append({"target": target, "method": method, "versions": nver,
                                         "bytes": len(text.encode()), "sha256": _hl.sha256(text.encode()).hexdigest()})
            continue
        variants = []
        for rp, otext, src in oracle_texts:
            oi, oh = P.top_items(otext)
            if oi:
                variants.append((rp, otext, oi, oh, src))
        if not variants:
            cands_w, wtag = (raw_path.get(target), "whole_path") if raw_path.get(target) else ((raw.get(base0) or []), "whole_base")
            if oracle_texts and cands_w:
                latest = max(cands_w, key=lambda x: x[0])[1]
                bestw = None
                for rp2, otext2, src2 in oracle_texts:
                    pw = round(P.sim(latest, otext2) * 100, 1)
                    if bestw is None or pw > bestw[0]:
                        bestw = (pw, rp2, src2)
                pw, rp2, src2 = bestw
                stage_db.record(con, [(target, "remote-v10", "actions_full_census", "WHOLE", pw,
                    f"remote run whole resolved={rp2} via={how}/{wtag}:{src2}")])
                summary["scored"] += 1
                summary["whole_scored"] += 1
                summary["rows"].append({"target": target, "resolved": rp2, "how": how + "/" + wtag, "pct": pw, "gaps": 0})
                continue
            summary["no_oracle"] += 1
            summary["gap_session"][session_state] += 1
            sub = "no_items" if oracle_texts else "oracle_miss"
            stage_db.record(con, [(target, "remote-v10", "actions_full_census", "WHOLE", None, f"NO_ORACLE:{how}:{sub}:session={session_state}")])
            summary["rows"].append({"target": target, "how": how, "gap": "NO_ORACLE", "sub": sub, "session": session_state})
            continue
        best = None
        for rp, otext, oitems, ohdr, src in variants:
            base = target.split("/")[-1]
            pool = {}
            for name in oitems:
                cs = by_hint.get((base, name)) or by_name.get(name) or []
                if cs:
                    pool[name] = [(ts, s2, ("", "", "")) for ts, s2 in cs]
            compose_for.oracle_text = otext
            composed, parts, gaps = compose_for(oitems, ohdr, pool, wholes.get(base))
            pct = round(P.sim(composed, otext) * 100, 1)
            if best is None or pct > best[0]:
                best = (pct, rp, oitems, parts, gaps, src, otext)
        pct, rp, oitems, parts, gaps, src, otext_best = best
        arb = ""
        if raw_path.get(target):
            latest_w = max(raw_path[target], key=lambda x: x[0])[1]
            pw2 = round(P.sim(latest_w, otext_best) * 100, 1)
            if pw2 > pct:
                arb = f" arbitrated:item={pct}"
                summary["rows"].append({"target": target, "resolved": rp, "how": how + "/whole_path", "pct": pw2, "gaps": len(gaps), "arbitrated_from": pct})
                rows = [(target, "remote-v10", "actions_full_census", "WHOLE", pw2,
                         f"remote run resolved={rp} via={how}/whole_path:{src}{arb}")]
                for n in oitems:
                    rows.append((target, "remote-v10", "actions_full_census", n,
                                 round(P.sim(parts[n], oitems[n]) * 100, 1) if n in parts else None, "remote run"))
                stage_db.record(con, rows)
                summary["scored"] += 1
                summary["whole_scored"] += 1
                continue
        rows = [(target, "remote-v10", "actions_full_census", "WHOLE", pct,
                 f"remote run resolved={rp} via={how}/{src}")]
        for n in oitems:
            rows.append((target, "remote-v10", "actions_full_census", n,
                         round(P.sim(parts[n], oitems[n]) * 100, 1) if n in parts else None, "remote run"))
        stage_db.record(con, rows)
        summary["scored"] += 1
        summary["rows"].append({"target": target, "resolved": rp, "how": how, "pct": pct, "gaps": len(gaps)})
    con.close()
    if gapfill_dir is not None:
        gapfill_dir.mkdir(parents=True, exist_ok=True)
        (gapfill_dir / "MANIFEST.json").write_text(json.dumps(
            {"stage": "remote-v10", "files": len(gapfill_rows), "rows": gapfill_rows}, indent=1))
        summary["gapfill"] = len(gapfill_rows)
    Path("remote_summary.json").write_text(json.dumps(summary, indent=1))
    print(f"targets={summary['targets']} scored={summary['scored']} no_oracle={summary['no_oracle']} fetch_fail={summary['fetch_fail']} gap_session={summary['gap_session']}")

if __name__ == "__main__":
    main()
