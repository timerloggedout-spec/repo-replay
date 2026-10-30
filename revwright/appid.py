#!/usr/bin/env python3
"""RevWright AppID method — token provider.
Collector (App 5535733) = READ bucket; Publisher (App 5537873) = WRITE bucket.
Mints installation tokens via the fleet connector helpers; tokens go to a
0600 temp file, never printed, never logged. Both apps are installed on
timerloggedout-spec/termux-monorepo ONLY today — calls to other repos fail
scope until the apps are installed there (recorded, not worked around).
"""
import subprocess, tempfile, os
from pathlib import Path

HOME = Path.home()
HELPERS = {
    "collector": HOME / "workspace/custom-connectors/custom.github-app-collector/bin/github_app_collector.py",
    "publisher": HOME / "workspace/custom-connectors/custom.github-app-publisher/bin/github_app_publisher.py",
}
INSTALLED = {"timerloggedout-spec/termux-monorepo", "timerloggedout-spec/repo-replay"}  # verified 2026-10-30T09:53Z via GET /installation/repositories on both app tokens

def mint(role: str) -> Path:
    """Return path to a 0600 file holding a fresh installation token."""
    fd, name = tempfile.mkstemp(prefix=f"revwright-{role}-")
    os.close(fd); os.chmod(name, 0o600)
    r = subprocess.run(["python3", str(HELPERS[role]), "mint", name],
                       capture_output=True, text=True)
    if r.returncode != 0:
        Path(name).unlink(missing_ok=True)
        raise RuntimeError(f"{role} mint failed (token not shown by design)")
    return Path(name)

def check_scope(repo: str) -> None:
    if repo not in INSTALLED:
        raise PermissionError(
            f"{repo}: AppID apps not installed here yet — owner installs "
            f"termux-fleet-collector + termux-fleet-publisher on the repo; "
            f"PAT is fallback only until then.")
