# AnyLog Docs

This is the technical documentation for [AnyLog Edge Data Fabric](https://www.anylog.network/), built with Jekyll and 
hosted on GitHub Pages.

This repository is the **backend** — it builds and serves the documentation site. The actual documentation content lives 
in a separate repository; see [Documentation Source](#documentation-source) below.

**Goal**: We decided to provide the documentation via a website at **https://anylog.network/docs** using Jekyll (same 
theme as OpenHorizon), replacing raw GitHub repo access with a structured, navigable site comparable to EdgeX or 
ReadTheDocs.

**Reference**: Source Repositories

| Repo | Default Branch | Purpose |
|---|---|---|
| [AnyLog-co/documentation](https://github.com/AnyLog-co/documentation) | main | Documentation content — source of truth, synced into this site |
| [AnyLog-co/anylog-docs.github.io](https://github.com/AnyLog-co/anylog-docs.github.io) | main | This repo — the Jekyll backend that builds and serves the site |


--- 

## Quick Start (Local Deployment)

1. Make sure you have `make`, `docker`, and `docker compose` installed.
2. Clone this repo (the backend) and the [content repository](https://github.com/AnyLog-co/documentation).
3. From this repo, start the docs locally, pointing `LOCAL_DOCS` at your local clone of the content repo:

```shell
make up LOCAL_DOCS=${PATH to documentation}

# Example
make up LOCAL_DOCS=/mnt/c/Users/oshad/AnyLog-docs/documentation
```

4. Open **http://localhost:4000** in your browser. Edits to files under `LOCAL_DOCS` are picked up live — no restart 
needed.

5. When you're done:

```shell
make down
```

> If `LOCAL_DOCS` is omitted, it defaults to `.` (this repo itself) — you almost always want to point it at your content 
> repo clone instead.

---

## Maintaining the Backend

This repo wraps a small Docker setup with a `Makefile` for convenience. The three pieces:

**`Makefile`** — the entry point for local development.

| Target  | What it does |
|---|---|
| `up`    | `docker compose up --build -d` — builds and starts the container |
| `down`  | `docker compose down` — stops the container |
| `logs`  | `docker logs -f anylog-docs` — follows the container's logs |
| `clean` | `docker compose down -v --rmi all` — stops the container and removes its volumes and images |
| `help`  | Prints usage (also the default target if you just run `make`) |

All targets accept `LOCAL_DOCS=<path>`. `up`, `down`, and `clean` validate that the path exists before doing anything (unless it's left at the default `.`).

**`docker-compose.yaml`** — defines a single `docs` service, built from the local `Dockerfile`:
- Exposes port `4000` (the Jekyll site) and `35729` (LiveReload).
- Runs `.github/scripts/dev-start.sh` as its startup command.
- Mounts `${LOCAL_DOCS:-.}` to `/srv/documentation` (the content source) and this repo to `/srv/content` (the Jekyll site itself), both `cached` for performance.
- Persists Bundler's gem cache in a named volume (`bundle-cache`) mounted at `/srv/bundle`, so `bundle install` doesn't rerun from scratch on every rebuild.

**`Dockerfile`** — built on `jekyll/jekyll:4`, with `python3` and `bash` installed for the repo's helper scripts. It 
runs as `root` to avoid gem-install and bundle permission issues; `BUNDLE_PATH` is set to `/srv/bundle` to match 
the compose volume above.

### Navigation / Sidebar Generation

Navigation is generated from the synced upstream files. The left sidebar section title is the folder that contains the 
Markdown file; root-level Markdown files are grouped under `Documentation`.

`.github/scripts/navigation.py` is now only used for optional ordering overrides for known slugs:

```python
ITEM_ORDER = {
    "Getting Started": [
        "getting-started",
        "installing-anylog",
        "my-topic"       # ← add your slug here
    ],
    ...
}
```

The slug is the synced path without the `.md` extension after the sync script normalizes spaces and punctuation. The 
sidebar display name is the synced filename without `.md`. The order of slugs within each section controls the order 
they appear in the sidebar.

`navigation.py` is consumed by `validate_docs.py`, which scans the generated `_docs/` directory and writes the `nav` 
block in `_config.yml`. This runs automatically on `docker compose up` and in GitHub Actions — you do not need to 
invoke it manually.

### Running Without Make

You can drive Docker Compose directly instead of going through `make`:

```bash
git clone https://github.com/AnyLog-co/anylog-docs.github.io.git
cd anylog-docs.github.io

LOCAL_DOCS=/path/to/AnyLog-co/documentation docker compose up --build -d
```

Open **http://localhost:4000**. To stop:

```bash
docker compose down
```

> Don't skip `LOCAL_DOCS` here — without it, the compose file falls back to mounting the current directory (this repo) 
> as the documentation source, which has no content to render.

**Troubleshooting:** If the container exits immediately with a bundle write-permissions error (`There was an error 
while trying to write to /srv/bundle`), clear the cached volume and retry:

```bash
docker compose down -v
docker compose up -d
```

The `-v` flag removes the cached volume so it gets recreated with the correct permissions.

### Local Mac Development

Use the local launcher when you want to run Jekyll directly on macOS without Docker:

```bash
python3 scripts/dev.py
```

The launcher pulls the external documentation, rebuilds `_docs/` and `_config.yml`, installs Bundler and gems into
`vendor/`, and starts Jekyll at **http://localhost:4000**.

macOS system Ruby is not supported for this project because it often lacks the headers needed to build Jekyll's native
gems. Use Ruby 3.x rather than Ruby 4 for GitHub Pages compatibility. Install Homebrew Ruby 3.3 first:

```bash
brew install ruby@3.3
python3 scripts/dev.py
```

Or let the launcher install Homebrew Ruby 3.3:

```bash
python3 scripts/dev.py --install-ruby
```

---

## Documentation Source

Documentation content is sourced from the public
<a href="https://github.com/AnyLog-co/documentation" target="_blank">AnyLog-co/documentation</a>
repository on the `main` branch.

Do not edit generated Markdown files in `_docs/` in this repository. The Jekyll build runs
`.github/scripts/sync_external_docs.py`, which clones `AnyLog-co/documentation`, converts every upstream `.md`
file into a Jekyll collection page, copies supporting assets into `assets/external-docs/`, and regenerates the sidebar
navigation.

The GitHub Pages workflow rebuilds on pushes and pull requests in this repository, manual workflow dispatch, an hourly
schedule, and `repository_dispatch` events of type `documentation-updated`.

For immediate publishing when `AnyLog-co/documentation` changes, add a workflow in that repository that sends a
`repository_dispatch` event to this repository after pushes to `main`. Without that dispatch, the scheduled rebuild
will still pick up upstream changes within the next hourly run.

**Editing documentation content itself — creating or updating pages, front matter, page IDs, and formatting 
conventions — happens in the content repo, not here:**
- Content repo: [AnyLog-co/documentation](https://github.com/AnyLog-co/documentation)
- How to update documentation: [HOWTO.md](https://github.com/AnyLog-co/documentation/blob/os-dev/HOWTO.md)

---

## Contributing

Changes to **this repository** (the Jekyll backend itself — templates, build scripts, `Makefile`, CI config, etc.) 
follow the same staged workflow as the content repo: this repository is implementing a change control process, so it 
follows a **PR-based workflow** against the **`pre-develop`** branch, not `main`. `main` is the published branch 
backing the live documentation URL (see [Documentation Source](#documentation-source)); changes land there once 
`pre-develop` is promoted to `main`.

**Required actions:**
- Find the file you want to update and branch/fork it from `pre-develop` (or create a new file)
- If you work locally:
  1. Make sure your local copy is in sync with `pre-develop`:
   ```bash
   git fetch origin
   git rebase origin/pre-develop
   ```
  2. Create a feature branch or fork the file, make your changes, then open a pull request **against `pre-develop`**

- Once edited, create a **pull request** for review and inclusion at the next update cycle

*Note:* direct pushes to `pre-develop` are blocked.
*Note 2:* merging into `pre-develop` does not publish immediately — the live site rebuilds once `pre-develop` is 
promoted to `main`.

> Content authoring conventions (page creation, front matter, permalinks, image paths) live in the content repo's 
> [HOWTO.md](https://github.com/AnyLog-co/documentation/blob/os-dev/HOWTO.md), not in this repository.