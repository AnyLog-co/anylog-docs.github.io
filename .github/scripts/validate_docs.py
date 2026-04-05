#!/usr/bin/env python3

import os
import yaml


class DirectoryNotFound(Exception):
    pass


class FileNotFound(Exception):
    pass


# ── Locate repo root ─────────────────────────────────────

ROOT = os.path.dirname(__file__).rsplit(".github", 1)[0]
if not os.path.isdir(ROOT) and not os.path.isdir:
    raise DirectoryNotFound(f"Failed to locate directory {ROOT}")

CONFIG = os.path.join(ROOT, "_config.yml")
print(CONFIG)
if not os.path.isfile(CONFIG):
    raise FileNotFound(f"Failed to locate configuration file: {CONFIG}")

DOCS_DIR = os.path.join(ROOT, "_docs")
if not os.path.isdir(DOCS_DIR):
    raise DirectoryNotFound(f"Failed to locate directory {DOCS_DIR}")


# ── Helpers ──────────────────────────────────────────────

def title_from_slug(slug: str) -> str:
    """Convert slug to human title."""
    return slug.replace("-", " ").replace("_", " ").title()


def section_title(dirname: str) -> str:
    """Convert directory name to section title."""
    return dirname.replace("-", " ").replace("_", " ").title()


# ── Load config ──────────────────────────────────────────

with open(CONFIG) as f:
    config = yaml.safe_load(f)

nav = config.setdefault("nav", [])


# Build lookup of existing slugs
existing_slugs = set()
for section in nav:
    for item in section.get("items", []):
        existing_slugs.add(item.get("slug"))


# ── Walk _docs directory ─────────────────────────────────

for section_dir in sorted(os.listdir(DOCS_DIR)):

    section_path = os.path.join(DOCS_DIR, section_dir)

    if not os.path.isdir(section_path):
        continue

    title = section_title(section_dir)

    # find or create section
    section = next((s for s in nav if s["title"] == title), None)

    if not section:
        section = {"title": title, "items": []}
        nav.append(section)

    items = section.setdefault("items", [])

    # scan markdown files
    for fname in sorted(os.listdir(section_path)):

        if not fname.endswith(".md"):
            continue

        slug = fname[:-3]

        if slug in existing_slugs:
            continue

        items.append({
            "slug": slug,
            "title": title_from_slug(slug)
        })

        existing_slugs.add(slug)

        print(f"Added nav entry: {title} → {slug}")


# ── Write updated config ─────────────────────────────────

with open(CONFIG, "w") as f:
    yaml.dump(config, f, sort_keys=False)

print("Navigation sync complete.")