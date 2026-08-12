#!/usr/bin/env python3

import os
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "_docs"
ASSETS_DIR = ROOT / "assets" / "external-docs"
WORK_DIR = ROOT / ".external-docs" / "documentation"

DOCS_REPO = os.environ.get("ANYLOG_DOCS_REPO", "https://github.com/AnyLog-co/documentation.git")
DOCS_REF = os.environ.get("ANYLOG_DOCS_REF", "main")
SOURCE_DIR = os.environ.get("ANYLOG_DOCS_SOURCE_DIR")

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
MD_LINK_RE = re.compile(r"(!?\[[^\]]*\]\()([^)]+)(\))")
HTML_SRC_RE = re.compile(r'((?:src|href)=["\'])([^"\']+)(["\'])')
LOOKUP_STOP_WORDS = {"a", "an", "the", "and", "or", "of", "to", "for", "in", "on", "with", "by", "as"}


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def slugify_component(value):
    value = value.strip()
    value = value.replace("&", " and ")
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-").lower() or "index"


def safe_relative_path(path):
    return Path(*[slugify_component(part) for part in path.parts])


def strip_order_prefix(value):
    value = re.sub(r"^\s*(?:\d+(?:-\d+)*|[A-Z])(?:\s*-\s*|\s+)", "", value)
    return value.strip() or value


def title_from_path(path):
    stem = strip_order_prefix(path.stem)
    stem = stem.replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in stem.split()) or "Untitled"


def lookup_tokens(value):
    value = unquote(str(value))
    value = value.replace("&", " and ")
    value = value.replace("_", " ").replace("-", " ")
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    value = re.sub(r"[^A-Za-z0-9]+", " ", value).lower()
    return [
        token
        for token in value.split()
        if token and not token.isdigit() and token not in LOOKUP_STOP_WORDS
    ]


def lookup_key(value):
    return "".join(lookup_tokens(value))


def suffix_lookup_keys(path):
    path = Path(path)
    parts = path.with_suffix("").parts
    keys = set()
    for start in range(len(parts)):
        key = lookup_key("/".join(parts[start:]))
        if key:
            keys.add(key)
    return keys


def split_front_matter(text):
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text

    front_matter = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        front_matter[key.strip()] = value.strip().strip('"').strip("'")
    return front_matter, text[match.end():]


def first_heading(text):
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return None


def remove_matching_first_heading(text, title):
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        match = re.match(r"^#\s+(.+?)\s*$", line.rstrip("\r\n"))
        if not match:
            continue

        if match.group(1).strip().casefold() != title.strip().casefold():
            return text

        del lines[index]
        if index < len(lines) and not lines[index].strip():
            del lines[index]
        return "".join(lines)

    return text


def is_external_url(target):
    parsed = urlsplit(target)
    return parsed.scheme in {"http", "https", "mailto", "tel"} or target.startswith("#")


def has_hidden_path_part(path):
    return any(re.match(r"^99(?:\b|[^A-Za-z0-9].*)", part) for part in Path(path).parts)


def source_checkout():
    if SOURCE_DIR:
        source = Path(SOURCE_DIR).expanduser().resolve()
        if not source.is_dir():
            raise FileNotFoundError(f"ANYLOG_DOCS_SOURCE_DIR does not exist: {source}")
        return source

    shutil.rmtree(WORK_DIR, ignore_errors=True)
    WORK_DIR.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", "--branch", DOCS_REF, DOCS_REPO, str(WORK_DIR)])
    return WORK_DIR


def should_skip_rel(rel):
    parts = rel.parts
    if any(part.startswith(".") for part in parts):
        return True

    if len(parts) == 1 and rel.name.lower() != "readme.md":
        return True

    if has_hidden_path_part(rel):
        return True
    top_level = parts[0] if parts else ""
    if top_level == "ORPHANS":
        return True

    upper_top_level = top_level.upper()
    if "INTERNAL" in upper_top_level or "DRAFT" in upper_top_level:
        return True

    return False


def iter_files(source):
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(source)
        if should_skip_rel(rel):
            continue
        yield path


def build_mappings(source):
    doc_map = {}
    asset_map = {}

    for path in iter_files(source):
        rel = path.relative_to(source)
        if path.suffix.lower() == ".md":
            safe_rel = safe_relative_path(rel.with_suffix(""))
            doc_map[rel] = {
                "output": DOCS_DIR / safe_rel.with_suffix(".md"),
                "url": "/docs/" + safe_rel.as_posix() + "/",
            }
        else:
            safe_rel = safe_relative_path(rel)
            asset_map[rel] = {
                "output": ASSETS_DIR / safe_rel,
                "url": "/assets/external-docs/" + safe_rel.as_posix(),
            }

    return doc_map, asset_map


def build_doc_lookup(doc_map):
    docs = []
    for rel, mapping in doc_map.items():
        output_rel = mapping["output"].relative_to(DOCS_DIR)
        aliases = set()
        aliases.update(suffix_lookup_keys(rel))
        aliases.update(suffix_lookup_keys(output_rel))

        basename_keys = {
            key
            for key in (
                lookup_key(rel.stem),
                lookup_key(output_rel.stem),
                lookup_key(title_from_path(rel)),
            )
            if key
        }
        aliases.update(basename_keys)

        docs.append(
            {
                "rel": rel,
                "url": mapping["url"],
                "aliases": aliases,
                "basename_keys": basename_keys,
                "section_key": lookup_key(rel.parts[0]) if rel.parts else "",
            }
        )
    return docs


def fallback_doc_target(current_rel, lookup_rel, doc_lookup):
    lookup_rel = Path(lookup_rel)
    full_key = lookup_key(lookup_rel.with_suffix("").as_posix())
    parent_key = lookup_key(lookup_rel.parent.as_posix()) if lookup_rel.parent != Path(".") else ""
    basename_key = lookup_key(lookup_rel.stem or lookup_rel.name)
    current_section_key = lookup_key(current_rel.parts[0]) if current_rel.parts else ""

    best_doc = None
    best_score = 0
    tied = False

    for doc in doc_lookup:
        score = 0
        aliases = doc["aliases"]

        if full_key:
            if full_key in aliases:
                score = max(score, 120)
            elif any(alias.endswith(full_key) for alias in aliases):
                score = max(score, 90)

        if basename_key:
            if basename_key in doc["basename_keys"]:
                score = max(score, 78)
            elif any(alias.endswith(basename_key) for alias in aliases):
                score = max(score, 62)

        if parent_key and any(parent_key in alias for alias in aliases):
            score += 10

        if current_section_key and current_section_key == doc["section_key"]:
            score += 4

        if score > best_score:
            best_doc = doc
            best_score = score
            tied = False
        elif score and score == best_score and best_doc and doc["url"] != best_doc["url"]:
            tied = True

    if not best_doc or tied or best_score < 70:
        return None

    return best_doc["url"]


def resolve_target(current_rel, target, doc_map, asset_map, doc_lookup):
    if is_external_url(target):
        return target

    split = urlsplit(target)
    raw_path = unquote(split.path)
    if not raw_path:
        return target
    if has_hidden_path_part(raw_path):
        return None

    source_root = Path("/source-root")
    if raw_path.startswith("/"):
        normalized = source_root / raw_path.lstrip("/")
    else:
        normalized = source_root / current_rel.parent / raw_path
    try:
        rel_candidate = normalized.resolve().relative_to(source_root)
    except ValueError:
        return target

    rel_candidate = Path(*rel_candidate.parts)
    lookup_candidate = rel_candidate
    if raw_path.startswith("/docs/"):
        lookup_candidate = Path(raw_path[len("/docs/"):].lstrip("/"))

    fragment = f"#{split.fragment}" if split.fragment else ""
    query = f"?{split.query}" if split.query else ""

    def liquid_relative_url(url):
        return "{{ " + json.dumps(url) + " | relative_url }}"

    if rel_candidate in doc_map:
        return liquid_relative_url(doc_map[rel_candidate]["url"] + fragment)

    if rel_candidate.suffix == "":
        if rel_candidate.name:
            md_candidate = rel_candidate.with_suffix(".md")
            if md_candidate in doc_map:
                return liquid_relative_url(doc_map[md_candidate]["url"] + fragment)

        for index_name in ("README.md", "readme.md", "Overview.md", "overview.md"):
            index_candidate = rel_candidate / index_name
            if index_candidate in doc_map:
                return liquid_relative_url(doc_map[index_candidate]["url"] + fragment)

    if rel_candidate in asset_map:
        return liquid_relative_url(asset_map[rel_candidate]["url"] + query + fragment)

    fallback_url = fallback_doc_target(current_rel, lookup_candidate, doc_lookup)
    if fallback_url:
        return liquid_relative_url(fallback_url + fragment)

    return target


def rewrite_links(text, current_rel, doc_map, asset_map, doc_lookup):
    def replace_md(match):
        resolved = resolve_target(current_rel, match.group(2), doc_map, asset_map, doc_lookup)
        if resolved is None:
            label = match.group(1)
            label_match = re.match(r"!?\[([^\]]*)\]\(", label)
            return label_match.group(1) if label_match else match.group(0)
        return match.group(1) + resolved + match.group(3)

    def replace_html(match):
        resolved = resolve_target(current_rel, match.group(2), doc_map, asset_map, doc_lookup)
        if resolved is None:
            return match.group(1) + "#" + match.group(3)
        return match.group(1) + resolved + match.group(3)

    text = remove_hidden_link_lines(text)
    text = MD_LINK_RE.sub(replace_md, text)
    text = HTML_SRC_RE.sub(replace_html, text)
    text = remove_hidden_link_lines(text)
    return text


def remove_hidden_link_lines(text):
    lines = []
    for line in text.splitlines(keepends=True):
        decoded = unquote(line)
        if "](" in line and has_hidden_path_part(decoded):
            continue
        lines.append(line)
    return "".join(lines)


def clean_readme_toc(text):
    lines = []
    in_toc = False

    def clean_markdown_labels(line):
        return re.sub(
            r"\[([^\[\]]+)\]",
            lambda match: "[" + strip_order_prefix(match.group(1)) + "]",
            line,
        )

    for line in text.splitlines(keepends=True):
        if "<!-- TOC:START" in line:
            in_toc = True
            lines.append(line)
            continue

        if "<!-- TOC:END" in line:
            in_toc = False
            lines.append(line)
            continue

        if in_toc:
            if has_hidden_path_part(unquote(line)):
                continue

            line = clean_markdown_labels(line)
            plain_item = re.match(r"^(\s*-\s+)([^\[\]\n]+?)(\r?\n?)$", line)
            if plain_item:
                line = plain_item.group(1) + strip_order_prefix(plain_item.group(2)) + plain_item.group(3)

        lines.append(line)

    return "".join(lines)


def enable_readme_markdown_in_html(text):
    return re.sub(
        r'<div(\s+align=["\']justified["\'])(?![^>]*\smarkdown=)',
        r'<div\1 markdown="1"',
        text,
        flags=re.IGNORECASE,
    )


def last_updated_for(source_root, rel):
    try:
        result = subprocess.run(
            ["git", "-C", str(source_root), "log", "-1", "--format=%cs", "--", rel.as_posix()],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""

    return result.stdout.strip()


def write_doc(source_root, source_path, rel, mapping, doc_map, asset_map, doc_lookup):
    raw = source_path.read_text(encoding="utf-8", errors="replace")
    existing_front_matter, body = split_front_matter(raw)
    if rel.as_posix().lower() == "readme.md":
        title = "Overview"
    else:
        title = strip_order_prefix(existing_front_matter.get("title") or first_heading(body) or title_from_path(rel))
    description = existing_front_matter.get("description", "")
    body = remove_matching_first_heading(body, title)
    body = rewrite_links(body, rel, doc_map, asset_map, doc_lookup)
    if rel.as_posix().lower() == "readme.md":
        body = enable_readme_markdown_in_html(body)
        body = clean_readme_toc(body)

    front_matter = [
        "---",
        f"title: {json.dumps(title)}",
        f"description: {json.dumps(description)}",
        "layout: page",
        f"source_path: {json.dumps(rel.as_posix())}",
        f"last_updated: {json.dumps(last_updated_for(source_root, rel))}",
        "---",
        "",
    ]

    output = mapping["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(front_matter) + body, encoding="utf-8")


def sync():
    source = source_checkout()
    doc_map, asset_map = build_mappings(source)
    doc_lookup = build_doc_lookup(doc_map)

    shutil.rmtree(DOCS_DIR, ignore_errors=True)
    shutil.rmtree(ASSETS_DIR, ignore_errors=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    for source_path in iter_files(source):
        rel = source_path.relative_to(source)
        if rel in doc_map:
            write_doc(source, source_path, rel, doc_map[rel], doc_map, asset_map, doc_lookup)
        elif rel in asset_map:
            output = asset_map[rel]["output"]
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, output)

    print(f"Synced {len(doc_map)} Markdown files from {DOCS_REPO}@{DOCS_REF}.")
    print(f"Copied {len(asset_map)} supporting files into {ASSETS_DIR.relative_to(ROOT)}.")


if __name__ == "__main__":
    try:
        sync()
    except Exception as exc:
        print(f"Failed to sync external docs: {exc}", file=sys.stderr)
        sys.exit(1)
