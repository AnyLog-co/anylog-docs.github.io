#!/usr/bin/env python3
"""
Audit _docs/ for broken file/image links and invalid anchors.

Repo layout:
  <repo-root>/
  ├── _docs/
  ├── assets/img/
  └── .github/scripts/audit/   ← this script

Usage:
  python3 audit_docs.py              # uses repo layout above
  python3 audit_docs.py /other/docs  # override docs dir
"""

import re
import sys
import os
import urllib.request
from pathlib import Path
from collections import defaultdict

from markdown_it import MarkdownIt

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT  = Path(os.path.dirname(__file__).split(".github")[0])
DOCS_DIR   = REPO_ROOT / "_docs"
ASSETS_DIR = REPO_ROOT / "assets" / "img"

CHECK_URLS  = True
URL_TIMEOUT = 5

md = MarkdownIt()


# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Match Jekyll's anchor slug generation."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text


def get_anchors(md_file: Path) -> set[str]:
    """Return the set of slugified heading anchors in a .md file."""
    tokens = md.parse(md_file.read_text(encoding="utf-8", errors="replace"))
    anchors = set()
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open":
            inline = tokens[i + 1]
            anchors.add(slugify(inline.content))
    return anchors


def get_links(md_file: Path) -> list[tuple[int, str]]:
    text   = md_file.read_text(encoding="utf-8", errors="replace")
    tokens = md.parse(text)
    links  = []

    for tok in tokens:
        if not tok.children or not tok.map:
            continue
        line_no = tok.map[0] + 1   # block token carries the line; pass to children
        for child in tok.children:
            if child.type in ("link_open", "image"):
                href = child.attrGet("href") or child.attrGet("src") or ""
                if href:
                    links.append((line_no, href))

    return links


def url_exists(url: str) -> bool:
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(
                url, method=method,
                headers={"User-Agent": "docs-auditor/1.0"},
            )
            with urllib.request.urlopen(req, timeout=URL_TIMEOUT) as r:
                return r.status < 400
        except Exception:
            continue
    return False


def resolve_file_link(raw: str, source_file: Path) -> bool:
    """
    Check that a local link resolves to a real file on disk.
    If an anchor is present, also verify it exists as a heading.
    """
    anchor = raw.split("#")[1] if "#" in raw else None
    target = raw.split("#")[0].split("?")[0].strip()

    # ── resolve file ──────────────────────────────────────────────────────
    if target:
        target_rel = target.lstrip("/")
        candidates = [
            source_file.parent / target_rel,   # sibling-relative
            REPO_ROOT   / target_rel,           # /assets/img/... etc.
            DOCS_DIR    / target_rel,           # bare doc reference
            ASSETS_DIR  / target_rel,           # bare image filename
        ]
        resolved = next(
            (p.resolve() for p in candidates if p.resolve().exists()), None
        )
        if resolved is None:
            return False
    else:
        resolved = source_file   # pure anchor on current file

    # ── validate anchor ───────────────────────────────────────────────────
    if anchor and resolved.suffix == ".md":
        if slugify(anchor) not in get_anchors(resolved):
            return False

    return True


# ── Main audit ────────────────────────────────────────────────────────────────

def audit(docs_dir: Path) -> dict[str, list[tuple[int, str]]]:
    """Return {file_key: [(line_no, broken_target), ...]}"""
    broken: dict[str, list[tuple[int, str]]] = defaultdict(list)

    for md_file in sorted(docs_dir.rglob("*.md")):
        rel_key = md_file.relative_to(docs_dir).with_suffix("").as_posix()

        for lineno, target in get_links(md_file):
            if target.startswith(("mailto:", "data:", "#", "{{")):
                continue

            if target.startswith(("http://", "https://", "ftp://")):
                if CHECK_URLS and not url_exists(target):
                    broken[rel_key].append((lineno, target))
            else:
                if not resolve_file_link(target, md_file):
                    broken[rel_key].append((lineno, target))

    return dict(broken)


# ── Output ────────────────────────────────────────────────────────────────────

def print_table(broken: dict[str, list[tuple[int, str]]]) -> None:
    if not broken:
        print("✅  No broken links found.")
        return

    col_file = max(len(k) for k in broken)
    col_file = max(col_file, len("File"))
    col_line = 6

    header = f"{'File':<{col_file}}  {'Line':<{col_line}}  Target"
    print(header)
    print("─" * len(header))

    for key in sorted(broken):
        for lineno, target in sorted(broken[key]):
            print(f"{key:<{col_file}}  {str(lineno):<{col_line}}  {target}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    docs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DOCS_DIR

    if not docs_dir.exists():
        print(f"Error: '{docs_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {docs_dir} ...\n")
    broken = audit(docs_dir)
    print_table(broken)


if __name__ == "__main__":
    main()