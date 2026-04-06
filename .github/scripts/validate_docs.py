#!/usr/bin/env python3

import os
import yaml

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

# ── Read `_config.yml` ─────────────────────────────────────
with open(CONFIG) as f:
    config = yaml.safe_load(f)

for nav in config["nav"]:
    print(nav)