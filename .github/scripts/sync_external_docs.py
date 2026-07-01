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
DOCS_REF = os.environ.get("ANYLOG_DOCS_REF", "master")
SOURCE_DIR = os.environ.get("ANYLOG_DOCS_SOURCE_DIR")

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
MD_LINK_RE = re.compile(r"(!?\[[^\]]*\]\()([^)]+)(\))")
HTML_SRC_RE = re.compile(r'((?:src|href)=["\'])([^"\']+)(["\'])')


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


def title_from_path(path):
    stem = path.stem.replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in stem.split()) or "Untitled"


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


def source_checkout():
    if SOURCE_DIR:
        source = Path(SOURCE_DIR).expanduser().resolve()
        if not source.is_dir():
            raise FileNotFoundError(f"ANYLOG_DOCS_SOURCE_DIR does not exist: {source}")
        return source

    shutil.rmtree(WORK_DIR, ignore_errors=True)
    WORK_DIR.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", "--depth", "1", "--branch", DOCS_REF, DOCS_REPO, str(WORK_DIR)])
    return WORK_DIR


def iter_files(source):
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.relative_to(source).parts:
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


def resolve_target(current_rel, target, doc_map, asset_map):
    if is_external_url(target):
        return target

    split = urlsplit(target)
    raw_path = unquote(split.path)
    if not raw_path:
        return target

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
    fragment = f"#{split.fragment}" if split.fragment else ""
    query = f"?{split.query}" if split.query else ""

    if rel_candidate in doc_map:
        return doc_map[rel_candidate]["url"] + fragment

    if rel_candidate.suffix == "":
        md_candidate = rel_candidate.with_suffix(".md")
        if md_candidate in doc_map:
            return doc_map[md_candidate]["url"] + fragment

    if rel_candidate in asset_map:
        return asset_map[rel_candidate]["url"] + query + fragment

    return target


def rewrite_links(text, current_rel, doc_map, asset_map):
    def replace_md(match):
        return match.group(1) + resolve_target(current_rel, match.group(2), doc_map, asset_map) + match.group(3)

    def replace_html(match):
        return match.group(1) + resolve_target(current_rel, match.group(2), doc_map, asset_map) + match.group(3)

    text = MD_LINK_RE.sub(replace_md, text)
    text = HTML_SRC_RE.sub(replace_html, text)
    return text


def write_doc(source_path, rel, mapping, doc_map, asset_map):
    raw = source_path.read_text(encoding="utf-8", errors="replace")
    existing_front_matter, body = split_front_matter(raw)
    title = existing_front_matter.get("title") or first_heading(body) or title_from_path(rel)
    description = existing_front_matter.get("description", "")
    body = remove_matching_first_heading(body, title)
    body = rewrite_links(body, rel, doc_map, asset_map)

    front_matter = [
        "---",
        f"title: {json.dumps(title)}",
        f"description: {json.dumps(description)}",
        "layout: page",
        f"source_path: {json.dumps(rel.as_posix())}",
        "---",
        "",
    ]

    output = mapping["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(front_matter) + body, encoding="utf-8")


def sync():
    source = source_checkout()
    doc_map, asset_map = build_mappings(source)

    shutil.rmtree(DOCS_DIR, ignore_errors=True)
    shutil.rmtree(ASSETS_DIR, ignore_errors=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    for source_path in iter_files(source):
        rel = source_path.relative_to(source)
        if rel in doc_map:
            write_doc(source_path, rel, doc_map[rel], doc_map, asset_map)
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
