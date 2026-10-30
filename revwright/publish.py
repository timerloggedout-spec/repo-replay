#!/usr/bin/env python3
"""RevWright publish — Publisher-bucket writes (AppID method).
Lands replay outputs + migration targets: branch -> files -> PR.
Publisher perms: contents=write, pull_requests=write, checks=read.
(No issues permission — coordination comments route via PR reviews.)
"""
import base64, json, urllib.request
from appid import mint, check_scope

API = "https://api.github.com"

def _call(token_file, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        "Authorization": f"Bearer {token_file.read_text().strip()}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read()) if r.length != 0 else {}

class Publisher:
    def __init__(self, repo: str):
        check_scope(repo)
        self.repo = repo
        self.tok = mint("publisher")
    def close(self): self.tok.unlink(missing_ok=True)
    def put_file(self, path, content: bytes, branch, message, sha=None):
        body = {"message": message, "branch": branch,
                "content": base64.b64encode(content).decode()}
        if sha: body["sha"] = sha
        return _call(self.tok, "PUT", f"/repos/{self.repo}/contents/{path}", body)
    def open_pr(self, head, base, title, body=""):
        return _call(self.tok, "POST", f"/repos/{self.repo}/pulls",
                     {"head": head, "base": base, "title": title, "body": body})
