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


def __order_items(section, items):
    order = [__slug_from_entry(e) for e in ITEM_ORDER.get(section, [])]
    if not order:
        return items

    ordered = []
    # Index by bare filename slug (last path component) so navigation.py entries
    # like "AnyLog-CLI" match items whose full slug is "CLI/AnyLog-CLI"
    remaining = {item["slug"].split("/")[-1]: item for item in items}

    for slug in order:
        if slug in remaining:
            ordered.append(remaining.pop(slug))

    ordered.extend(remaining.values())
    return ordered


def __order_sections(nav_dict, section_order):
    ordered = []
    for section in section_order:
        if section in nav_dict:
            items = __order_items(section, nav_dict[section])
            ordered.append({"title": section, "items": items})

    for section, items in nav_dict.items():
        if section not in section_order:
            ordered.append({"title": section, "items": items})

    return ordered


def __dict_to_nav_list(nav_dict):
    nav_list = __order_sections(nav_dict, ITEM_ORDER)
    return nav_list


# ── Read `_config.yml` ────────────────────────────────────

with open(CONFIG) as f:
    config = yaml.safe_load(f)

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
                # Include subfolder in slug so sidebar.html builds the correct URL
                # e.g. "CLI/AnyLog-CLI" -> /docs/CLI/AnyLog-CLI/
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

navs = copy.deepcopy(ROOT_PATHS)
for key in ROOT_PATHS:
    if not navs.get(key) and navs.get(key) is not None:
        navs.pop(key)
ROOT_PATHS = copy.deepcopy(navs)

# ── Write updated `_config.yml` ───────────────────────────

config["nav"] = __dict_to_nav_list(nav_dict=ROOT_PATHS)
with open(CONFIG, 'w') as f:
    yaml.dump(config, f, sort_keys=False)

print("Navigation sync complete.")