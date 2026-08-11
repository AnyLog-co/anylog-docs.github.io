#!/usr/bin/env python3

from pathlib import Path

from navigation import ITEM_ORDER


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


def titleize(value):
    value = value.replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in value.split()) or "Documentation"


def slug_from_entry(entry):
    if isinstance(entry, dict):
        return entry["slug"]
    return entry


def nav_title_for(source_path):
    if source_path.name.lower() == "readme.md":
        return "Overview"
    return source_path.stem


def order_items(section, items):
    overview_items = [item for item in items if item.get("is_overview")]
    items = [item for item in items if not item.get("is_overview")]

    order = [slug_from_entry(e) for e in ITEM_ORDER.get(section, [])]
    if not order:
        return overview_items + sorted(items, key=lambda item: item["title"].lower())

    ordered = []
    remaining = {item["slug"].split("/")[-1]: item for item in items}
    for slug in order:
        if slug in remaining:
            ordered.append(remaining.pop(slug))

    ordered.extend(sorted(remaining.values(), key=lambda item: item["title"].lower()))
    return overview_items + ordered


def order_sections(nav_dict):
    preferred = list(ITEM_ORDER.keys())
    if "Documentation" in nav_dict and "Documentation" not in preferred:
        preferred.insert(0, "Documentation")

    ordered = []
    for section in preferred:
        if section in nav_dict:
            ordered.append({"title": section, "items": order_items(section, nav_dict[section])})

    for section in sorted(nav_dict):
        if section not in preferred:
            ordered.append({"title": section, "items": order_items(section, nav_dict[section])})

    return ordered


def source_path_for(md_path, rel_path):
    source_path = read_front_matter(md_path).get("source_path")
    if source_path:
        return Path(source_path)
    return rel_path


def section_for(source_path):
    if source_path.parent == Path("."):
        return "Documentation"
    return titleize(source_path.parent.name)


<<<<<<< Updated upstream
def discover_docs():
    nav = {}
=======
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

    if len(parts) == 1 and source_path.name.lower() != "readme.md":
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

>>>>>>> Stashed changes
    for md_path in sorted(DOCS_DIR.rglob("*.md")):
        rel = md_path.relative_to(DOCS_DIR)
        source_path = source_path_for(md_path, rel)
        section = section_for(source_path)
        slug = rel.with_suffix("").as_posix()
        nav.setdefault(section, []).append({
            "slug": slug,
            "title": nav_title_for(source_path),
            "file": rel.as_posix(),
            "is_overview": source_path.name.lower() == "readme.md",
        })
    return nav


def config_without_nav():
    lines = CONFIG.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line == "nav:":
            return "\n".join(lines[:index]).rstrip() + "\n"
    return "\n".join(lines).rstrip() + "\n"


def yaml_quote(value):
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_nav(nav):
    lines = ["nav:"]
    for section in nav:
        lines.append(f"- title: {yaml_quote(section['title'])}")
        lines.append("  items:")
        for item in section["items"]:
            lines.append(f"  - slug: {yaml_quote(item['slug'])}")
            lines.append(f"    title: {yaml_quote(item['title'])}")
            lines.append(f"    file: {yaml_quote(item['file'])}")
    return "\n".join(lines) + "\n"


def main():
    if not ROOT.is_dir():
        raise DirectoryNotFound(f"Failed to locate repository root: {ROOT}")
    if not CONFIG.is_file():
        raise FileNotFound(f"Failed to locate configuration file: {CONFIG}")
    if not DOCS_DIR.is_dir():
        raise DirectoryNotFound(f"Failed to locate docs directory: {DOCS_DIR}")

    CONFIG.write_text(config_without_nav() + render_nav(order_sections(discover_docs())), encoding="utf-8")

    print("Navigation sync complete.")


if __name__ == "__main__":
    main()
