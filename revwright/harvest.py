#!/usr/bin/env python3
"""RevWright harvest — Collector-bucket reads (AppID method).
Reads session-export trees via the Contents API on the Collector token,
feeding extract.py. Source reads for migrations use this same path.
"""
import json, urllib.request
from appid import mint, check_scope

API = "https://api.github.com"

def _get(token_file, path):
    req = urllib.request.Request(API + path, headers={
        "Authorization": f"Bearer {token_file.read_text().strip()}",
        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def list_tree(repo: str, ref: str = "master"):
    check_scope(repo)
    tok = mint("collector")
    try:
        return _get(tok, f"/repos/{repo}/git/trees/{ref}?recursive=1")["tree"]
    finally:
        tok.unlink(missing_ok=True)

if __name__ == "__main__":
    import sys
    t = list_tree(sys.argv[1] if len(sys.argv) > 1 else "timerloggedout-spec/termux-monorepo")
    print(f"paths={len(t)}")
