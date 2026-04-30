"""
Fetches CHANGELOG.md from the pre-develop branch of each source repo
and writes them into _docs/Version-Control/ in the docs repo.

Triggered by sync-changelogs.yml (schedule, manual, or repository_dispatch).
Requires GH_TOKEN env var set to the shared PAT.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
# from pathlib import Path

SOURCES = [
    {
        "repo":   "AnyLog-co/AnyLog-Network",
        "branch": "pre-develop",
        "file":   "CHANGELOG.md",
        "dest":   "_docs/Version-Control/SOURCE-CHANGELOGS.md",
    },
    {
        "repo":   "AnyLog-co/docker-compose",
        "branch": "pre-develop",
        "file":   "CHANGELOG.md",
        "dest":   "_docs/Version-Control/DOCKER_COMPOSE-CHANGELOG.md",
    },
    {
        "repo":   "AnyLog-co/deployment-scripts",
        "branch": "pre-develop",
        "file":   "CHANGELOG.md",
        "dest":   "_docs/Version-Control/DEPLOYMENT_SCRIPTS-CHANGELOGS.md",
    },
]

GITHUB_API = "https://api.github.com"
TOKEN      = os.environ.get("GH_TOKEN", "")

if not TOKEN:
    print("✗ GH_TOKEN is not set")
    sys.exit(1)


def fetch_file(repo: str, branch: str, filepath: str) -> str | None:
    url = f"{GITHUB_API}/repos/{repo}/contents/{filepath}?ref={branch}"
    req = urllib.request.Request(url, headers={
        "Accept":               "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization":        f"Bearer {TOKEN}",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"  ✗ HTTP {exc.code} — {repo}/{filepath}@{branch}: {exc.reason}")
        return None

    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8")
    return data.get("content")


def ensure_front_matter(content: str, source: dict) -> str:
    """Prepend Jekyll front matter if the upstream file doesn't already have it."""
    if content.lstrip().startswith("---"):
        return content