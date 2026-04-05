#!/usr/bin/env python3
"""
Validates two things before the Jekyll build:
  1. Every slug in _config.yml nav has a matching file in _docs/
     Every file in _docs/ is listed in the nav (warning, not error)
  2. Every internal /docs/slug link in any .md file resolves to a real doc
"""

import os
import re
import sys
import yaml

ROOT = os.path.dirname(__file__)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__.split("")))))
CONFIG = os.path.join(ROOT, "_config.yml")
DOCS_DIR = os.path.join(ROOT, "_docs")

errors = []
warnings = []

# ── 1. list _docs file paths ──────────────────────
if not os.path.isdir(DOCK)


# ── 1. Load nav slugs from _config.yml ────────────────────────────────────────

with open(CONFIG) as f:
    config = yaml.safe_load(f)

nav_slugs = {}  # slug -> section title
for section in config.get("nav", []):
    for item in section.get("items", []):
        slug = item.get("slug", "").strip()
        if slug:
            nav_slugs[slug] = section.get("title", "unknown")


# ── 2. Collect doc files ───────────────────────────────────────────────────────

doc_files = set()
if os.path.isdir(DOCS_DIR):
    for fname in os.listdir(DOCS_DIR):
        if fname.endswith(".md"):
            doc_files.add(fname[:-3])


# ── 3. ToC checks ─────────────────────────────────────────────────────────────

# Nav entry with no matching file → error
for slug, section in sorted(nav_slugs.items()):
    if slug not in doc_files:
        errors.append(
            "[ToC]   nav slug '{}' (section: {}) has no matching _docs/{}.md".format(
                slug, section, slug
            )
        )

# File in _docs with no nav entry → warning only (allows staging files)
for slug in sorted(doc_files - set(nav_slugs.keys())):
    warnings.append(
        "[ToC]   _docs/{}.md exists but is not listed in _config.yml nav".format(slug)
    )


# ── 4. Internal link checks ───────────────────────────────────────────────────

# Match [text](/docs/slug) or [text](/docs/slug/) with optional #anchor
LINK_RE = re.compile(r"\[([^\]]+)\]\(/docs/([^/#\s)]+)\/?(?:#[^)]+)?\)")

for fname in sorted(os.listdir(DOCS_DIR)):
    if not fname.endswith(".md"):
        continue
    filepath = os.path.join(DOCS_DIR, fname)
    with open(filepath) as f:
        lines = f.readlines()
    for lineno, line in enumerate(lines, 1):
        for m in LINK_RE.finditer(line):
            # slug = m.group(3).strip("/")
            slug = m.group(2)
            href = "/docs/" + slug
            if slug not in doc_files:
                errors.append(
                    "[Links] {}:{} — broken link '{}' (no _docs/{}.md)".format(
                        fname, lineno, href, slug
                    )
                )


# ── 5. Report ─────────────────────────────────────────────────────────────────

if warnings:
    print("Warnings (not blocking):")
    for w in warnings:
        print("  WARNING  " + w)
    print()

if errors:
    print("Errors:")
    for e in errors:
        print("  ERROR  " + e)
    print()
    print("{} error(s). Fix before merging.".format(len(errors)))
    sys.exit(1)

print("OK  ToC valid    — {} nav entries, {} doc files".format(len(nav_slugs), len(doc_files)))
print("OK  Links valid  — no broken internal references")
if warnings:
    print("    {} warning(s) — files in _docs not yet in nav".format(len(warnings)))