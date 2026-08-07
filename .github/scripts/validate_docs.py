#!/usr/bin/env python3

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "_config.yml"
DOCS_DIR = ROOT / "_docs"


class DirectoryNotFound(Exception):
    pass


class FileNotFound(Exception):
    pass


def read_front_matter(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"):
        return {}

    _, front_matter, _ = text.split("---", 2)
    values = {}
    for line in front_matter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def source_path_for(md_path, rel_path):
    source_path = read_front_matter(md_path).get("source_path")
    if source_path:
        return Path(source_path)
    return rel_path


def page_title_for(source_path):
    if source_path.name.lower() == "readme.md":
        return "Overview"
    return strip_order_prefix(source_path.stem)


def strip_order_prefix(value):
    value = re.sub(r"^\s*(?:\d+(?:-\d+)*|[A-Z])(?:\s*-\s*|\s+)", "", value)
    return value.strip() or value


def folder_title_for(path):
    name = path.name or "Documentation"
    return strip_order_prefix(name)


def should_include_source_path(source_path):
    parts = source_path.parts
    if any(part.startswith(".") for part in parts):
        return False

    if any(re.match(r"^99(?:\b|[^A-Za-z0-9].*)", part) for part in parts):
        return False
    top_level = parts[0] if parts else ""
    if top_level == "ORPHANS":
        return False

    upper_top_level = top_level.upper()
    if "INTERNAL" in upper_top_level or "DRAFT" in upper_top_level:
        return False

    return True


def natural_key(value):
    parts = re.split(r"(\d+)", value.casefold())
    return [int(part) if part.isdigit() else part for part in parts]


def source_order_key(value):
    match = re.match(r"^\s*(\d+(?:-\d+)*)(?:\s*-\s*|\s+)", value)
    if not match:
        return (1, (), natural_key(value))

    order = tuple(int(part) for part in match.group(1).split("-"))
    title = value[match.end():].strip()
    return (0, order, natural_key(title))


def sort_entries(entries):
    def key(entry):
        if entry["kind"] == "page" and entry.get("is_overview"):
            return (0, (), (), ())

        sort_key = entry.get("sort_key", entry["title"])
        kind_order = 0 if entry["kind"] == "section" else 1
        return (1, source_order_key(sort_key), kind_order, natural_key(entry["title"]))

    return sorted(entries, key=key)


def ensure_section(container, source_folder, safe_folder):
    sections = container.setdefault("sections", {})
    key = source_folder.as_posix()
    section = sections.get(key)
    if section:
        return section

    section = {
        "kind": "section",
        "title": folder_title_for(source_folder),
        "sort_key": source_folder.name,
        "match_path": "/docs/" + safe_folder.as_posix().strip("/") + "/" if safe_folder.parts else "/docs/",
        "children": [],
        "sections": {},
    }
    sections[key] = section
    container["children"].append(section)
    return section


def discover_tree():
    root = {"children": [], "sections": {}}

    for md_path in sorted(DOCS_DIR.rglob("*.md")):
        rel = md_path.relative_to(DOCS_DIR)
        source_path = source_path_for(md_path, rel)
        if not should_include_source_path(source_path):
            continue
        safe_path = rel.with_suffix("")

        container = root
        source_parts = list(source_path.parts[:-1])
        safe_parts = list(safe_path.parts[:-1])

        for index, folder_name in enumerate(source_parts):
            source_folder = Path(*source_parts[: index + 1])
            safe_folder = Path(*safe_parts[: index + 1])
            container = ensure_section(container, source_folder, safe_folder)

        container["children"].append(
            {
                "kind": "page",
                "title": page_title_for(source_path),
                "sort_key": source_path.name,
                "slug": safe_path.as_posix(),
                "url": "/docs/" + safe_path.as_posix() + "/",
                "match_path": "/docs/" + safe_path.as_posix() + "/",
                "file": rel.as_posix(),
                "source_path": source_path.as_posix(),
                "is_overview": source_path.name.lower() == "readme.md",
            }
        )

    finalize_tree(root)
    return root["children"]


def finalize_tree(node):
    children = []
    for child in node["children"]:
        if child["kind"] == "section":
            finalize_tree(child)
            child.pop("sections", None)
        children.append(child)

    node["children"] = sort_entries(children)


def config_without_nav():
    lines = CONFIG.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line == "nav:":
            return "\n".join(lines[:index]).rstrip() + "\n"
    return "\n".join(lines).rstrip() + "\n"


def yaml_quote(value):
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_nodes(nodes, indent=0):
    lines = []
    prefix = "  " * indent
    for node in nodes:
        lines.append(f"{prefix}- kind: {yaml_quote(node['kind'])}")
        lines.append(f"{prefix}  title: {yaml_quote(node['title'])}")
        lines.append(f"{prefix}  match_path: {yaml_quote(node['match_path'])}")
        if node["kind"] == "page":
            lines.append(f"{prefix}  slug: {yaml_quote(node['slug'])}")
            lines.append(f"{prefix}  url: {yaml_quote(node['url'])}")
            lines.append(f"{prefix}  file: {yaml_quote(node['file'])}")
            lines.append(f"{prefix}  source_path: {yaml_quote(node['source_path'])}")
        else:
            lines.append(f"{prefix}  children:")
            lines.extend(render_nodes(node["children"], indent + 2))
    return lines


def render_nav(nodes):
    lines = ["nav:"]
    lines.extend(render_nodes(nodes, 0))
    return "\n".join(lines) + "\n"


def main():
    if not ROOT.is_dir():
        raise DirectoryNotFound(f"Failed to locate repository root: {ROOT}")
    if not CONFIG.is_file():
        raise FileNotFound(f"Failed to locate configuration file: {CONFIG}")
    if not DOCS_DIR.is_dir():
        raise DirectoryNotFound(f"Failed to locate docs directory: {DOCS_DIR}")

    CONFIG.write_text(config_without_nav() + render_nav(discover_tree()), encoding="utf-8")
    print("Navigation sync complete.")


if __name__ == "__main__":
    main()
