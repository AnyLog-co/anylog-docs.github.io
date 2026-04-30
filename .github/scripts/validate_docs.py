#!/usr/bin/env python3

import re
import os
import yaml
import copy
import posixpath

from navigation import ITEM_ORDER

# Map filesystem folder names to ITEM_ORDER section keys
# Add an entry here whenever a new _docs/ subfolder is created
FOLDER_TO_SECTION = {
    "Getting-Started":            "Getting Started",
    "CLI":                        "CLI",
    "Network-Services":           "Network & Services",
    "Managing-Data-Southbound":   "Managing Data (Southbound)",
    "Querying-Data-Northbound":   "Querying Data (Northbound)",
    "Monitoring-Operations":      "Monitoring & Operations",
    "Tools-UI":                   "Tools & UI",
    "Version-Control":            "Version Control",
    "Reference":                  "Reference",
}


# ── Locate repo root ─────────────────────────────────────
class DirectoryNotFound(Exception):
    pass


class FileNotFound(Exception):
    pass


ROOT = os.path.dirname(__file__).rsplit(".github", 1)[0]
if not os.path.isdir(ROOT) and not os.path.isdir:
    raise DirectoryNotFound(f"Failed to locate directory {ROOT}")

CONFIG = os.path.join(ROOT, "_config.yml")
if not os.path.isfile(CONFIG):
    raise FileNotFound(f"Failed to locate configuration file: {CONFIG}")

DOCS_DIR = os.path.join(ROOT, "_docs")
if not os.path.isdir(DOCS_DIR):
    raise DirectoryNotFound(f"Failed to locate directory {DOCS_DIR}")


# ── Support functions ─────────────────────────────────────

def __extract_title(md_path):
    """Extract `title` from YAML front matter of a Markdown file."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL | re.MULTILINE)
    if match:
        for line in match.group(1).splitlines():
            if line.strip().startswith("title:"):
                return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def __nav_title_override(section, slug):
    """
    Return a title override for a slug if navigation.py defines one.

    ITEM_ORDER entries can be either a plain slug string:
        "getting-started"
    or a dict with an explicit title:
        {"slug": "getting-started", "title": "Getting Started Guide"}

    If a dict form is used, that title takes precedence over the front matter title.
    """
    for entry in ITEM_ORDER.get(section, []):
        if isinstance(entry, dict) and entry.get("slug") == slug:
            return entry.get("title")
    return None


def __slug_from_entry(entry):
    """Normalise a navigation.py entry to just its slug string."""
    if isinstance(entry, dict):
        return entry["slug"]
    return entry


def __existing_nav_index(existing_nav: list) -> dict:
    """
    Build a lookup of what's already in _config.yml nav.
    Returns: { section_title: { bare_slug: item_dict } }
    """
    index = {}
    for section in existing_nav or []:
        title = section.get("title", "")
        index[title] = {}
        for item in section.get("items", []):
            bare = item.get("slug", "").split("/")[-1]
            index[title][bare] = item
    return index


def __merge_nav(existing_nav: list, discovered: dict) -> list:
    """
    Core logic: _config.yml is the source of truth.

    Rules:
    - Every item already in _config.yml stays exactly where it is.
    - Items found on disk but NOT in _config.yml are appended to their section.
    - Sections in ITEM_ORDER but not yet in _config.yml are appended at the end.
    - Nothing is removed or reordered.
    """
    # Build fast lookup of what's already in config
    existing_index = __existing_nav_index(existing_nav)

    # Work on a copy so we don't mutate the original
    result = copy.deepcopy(existing_nav) if existing_nav else []

    # Index result sections by title for fast append
    result_section_index = {s["title"]: s for s in result}

    for section_title, items in discovered.items():
        existing_slugs = existing_index.get(section_title, {})

        new_items = []
        for item in items:
            bare = item["slug"].split("/")[-1]
            if bare not in existing_slugs:
                new_items.append(item)
                print(f"  + Adding to nav: [{section_title}] {bare}")

        if not new_items:
            continue

        if section_title in result_section_index:
            # Section exists — append missing items at end of it
            result_section_index[section_title]["items"].extend(new_items)
        else:
            # Brand new section — append at end of nav
            result.append({"title": section_title, "items": new_items})
            result_section_index[section_title] = result[-1]
            print(f"  + Adding new section to nav: {section_title}")

    return result


# ── Read `_config.yml` ────────────────────────────────────

with open(CONFIG) as f:
    config = yaml.safe_load(f)

existing_nav = config.get("nav", [])

# ── Walk `_docs/` ─────────────────────────────────────────

ROOT_PATHS = {}
for root, _, file in os.walk(DOCS_DIR):
    folder_name = "root"
    if root:
        if '/' in root:
            folder_name = root.rsplit('/', 1)[-1]
        elif '\\' in root:
            folder_name = root.rsplit('\\', 1)[-1]
    # Translate folder name to ITEM_ORDER section key; fall back to folder name
    dir_name = FOLDER_TO_SECTION.get(folder_name, folder_name)
    if ROOT_PATHS.get(dir_name) is None:
        ROOT_PATHS[dir_name] = []

    if file and isinstance(file, list):
        for fname in file:
            if not (fname.endswith(".") or fname == "README.md"):
                bare_slug = os.path.splitext(fname)[0]
                slug = posixpath.join(folder_name, bare_slug) if folder_name != "root" else bare_slug
                nav_title = __nav_title_override(dir_name, bare_slug)
                file_title = __extract_title(md_path=os.path.join(root, fname))
                ROOT_PATHS[dir_name].append({
                    "slug": slug,
                    "title": nav_title or file_title,
                    "file": posixpath.join(folder_name, fname)
                })
    elif file and not (file.endswith(".") or file == "README.md"):
        slug = os.path.splitext(file)[0]
        nav_title = __nav_title_override("root", slug)
        file_title = __extract_title(md_path=os.path.join(DOCS_DIR, file))
        ROOT_PATHS[dir_name].append({
            "slug": slug,
            "title": nav_title or file_title,
            "file": posixpath.join(file)
        })

# Drop empty sections
ROOT_PATHS = {k: v for k, v in ROOT_PATHS.items() if v}

# ── Merge: config is source of truth, only add what's missing ────────────────

config["nav"] = __merge_nav(existing_nav, ROOT_PATHS)

with open(CONFIG, 'w') as f:
    yaml.dump(config, f, sort_keys=False)

print("Navigation sync complete.")