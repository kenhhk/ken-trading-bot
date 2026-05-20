"""Git commit + push for the stateless GitHub Actions runner pattern."""

import os
import subprocess
from typing import Iterable


GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "kenhhk/ken-trading-bot")
BOT_EMAIL = "bot@ken-trading-bot.com"
BOT_NAME = "Ken Trading Bot"


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"[git] $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def commit_and_push(files: Iterable[str], message: str) -> bool:
    """Stage given files, commit, push. Returns True on success, False if nothing to commit."""
    files = list(files)
    _run(["git", "config", "user.email", BOT_EMAIL])
    _run(["git", "config", "user.name", BOT_NAME])
    for f in files:
        _run(["git", "add", f], check=False)

    # Check if anything is staged
    diff = _run(["git", "diff", "--cached", "--quiet"], check=False)
    if diff.returncode == 0:
        print("[git] nothing to commit")
        return False

    _run(["git", "commit", "-m", message])

    if GITHUB_TOKEN:
        push_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
        # Rebase-pull to avoid conflicts with parallel jobs
        _run(["git", "pull", "--rebase", push_url, "main"], check=False)
        result = _run(["git", "push", push_url, "HEAD:main"], check=False)
        if result.returncode != 0:
            print(f"[git] push FAILED: {result.stderr}")
            return False
        print("[git] pushed")
    else:
        _run(["git", "push", "origin", "HEAD:main"], check=False)
    return True
