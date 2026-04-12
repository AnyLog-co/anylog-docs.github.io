# AnyLog Documentation Project — Status Report
_Last updated: April 2026_

---
 
## Goal
 
Build a proper documentation website at **https://anylog.network/docs** using Jekyll (same theme as OpenHorizon), replacing raw GitHub repo access with a structured, navigable site comparable to EdgeX or ReadTheDocs.
 
---
 
## Source repositories
 
| Repo | Purpose | Status |
|---|---|---|
| **https://github.com/AnyLog-co/documentation** | Old docs — ~279 files, comprehensive but unorganised, not a website | Source of truth for migration |
| **EdgeLake documentation site** | Ori's first Jekyll attempt — limited, semi-organised | To be deprecated |
| **https://github.com/AnyLog-co/anylog-docs.github.io** (branch: `os-dev`) | New Jekyll site — active development | Work in progress |
 
---
 
## Version control
 
| Item | Status |
|---|---|
| `CHANGELOG.md` for AnyLog-Network (source) — auto-updates with "Unreleased" content | ✅ Done |
| `CHANGELOG.md` for deployment-scripts — automation needs testing/verification | ⚠️ Needs verification |

---

## Current file inventory — `_docs/` (os-dev)

### _docs/Getting Started/
| File | Source | Status |
|---|---|---|
| `getting-started.md` | Introduction to AnyLog slides | ✅ In repo |
| `installing-anylog.md` | Technical Training slides | ✅ In repo |
| `install-ova.md` | `anylog-demo-ova-scripts` README + install scripts | ✅ In repo |
| `anylog-as-service.md` | Old `deployments/AnyLog_as_Service.md` | ✅ In repo |
| `deployment-scripts.md` | Deployment Scripts slides | ✅ In repo |

### _docs/CLI/
| File | Source | Status |
|---|---|---|
| `AnyLog-CLI.md` | Old `cli.md` + new content | ✅ In repo — needs trim (overlaps with get-cmds.md) |
| `node-status.md` | New | ✅ In repo |
| `get-cmds.md` | Old `monitoring nodes.md` + new content | ✅ In repo |

### _docs/Network & Services/
| File | Source | Status |
|---|---|---|
| `background-services.md` | Old `background processes.md` — improved | ✅ In repo |
| `blockchain.md` | Old `blockchain commands.md` + `blockchain configuration.md` | ✅ In repo |
| `network-configurations.md` | Old `network configuration.md` | ✅ In repo |
| `policies-and-metadata.md` | Old `policies.md` + `metadata management.md` | ❌ Written, not yet committed to repo |

### _docs/Managing Data (Southbound)/
| File | Source | Status |
|---|---|---|
| `overview.md` | New — southbound pipeline overview | ✅ In repo |
| `data-ingestion.md` | Old `adding data.md` + `message broker.md` | ✅ In repo |
| `opcua.md` | Old `opcua.md` + `enthernetip.md` | ✅ In repo |
| `grpc.md` | Old `using grpc.md` | ✅ In repo |
| `node-red.md` | Old `node_red.md` | ✅ In repo |
| `syslog.md` | Old `using syslog.md` | ✅ In repo |
| `video-streaming.md` | Old `video streaming.md` | ✅ In repo |
| `live-data-generator.md` | Data Generator slides | ✅ In repo |
| `edgex.md` | Old `using edgex.md` | ✅ In repo |

### _docs/Querying Data (Northbound)/
| File | Source | Status |
|---|---|---|
| `overview.md` | New — northbound query overview | ✅ In repo |
| `queries.md` | Old `queries.md` | ✅ In repo |
| `sql-setup.md` | Old `sql setup.md` | ✅ In repo |
| `using-rest.md` | Old `using rest.md` | ✅ In repo |
| `grafana.md` | Old `northbound connectors/using grafana.md` | ✅ In repo |
| `import-grafana-dashboard.md` | Old grafana import guide | ✅ In repo |
| `PowerBI.md` | Old `northbound connectors/PowerBI.md` | ✅ In repo — stub, needs content |
| `Qlik.md` | Old `northbound connectors/Qlik.md` | ✅ In repo — stub, needs content |
| `Google.md` | Old `northbound connectors/Google.md` | ✅ In repo — stub, needs content |
| `postgres-connector.md` | Old `northbound connectors/postgres connector.md` | ✅ In repo — stub, needs content |
| `notification.md` | Old `northbound connectors/notifciation.md` | ✅ In repo — stub, needs content |
| `node-red.md` | New | ✅ In repo |
| `README.md` | — | ⚠️ Delete — validate_docs.py skips it; `overview.md` is the correct file |

### _docs/Monitoring & Operations/
| File | Source | Status |
|---|---|---|
| `node-monitoring.md` | Old `monitoring nodes.md` + `alerts and monitoring.md` + streaming conditions | ✅ In repo |
| `aggregations.md` | Old `aggregations.md` | ✅ In repo |
| `high-availability.md` | Old `high availability.md` | ✅ In repo |

### _docs/Tools & UI/
| File | Source | Status |
|---|---|---|
| `mcp.md` | New — MCP server | ✅ In repo |
| `remote-gui.md` | Remote GUI slides + old `remote_cli.md` | ✅ In repo |

### _docs/Reference/
| File | Source | Status |
|---|---|---|
| `FAQ.md` | Old `Tips & Tricks/` + `common_issues.md` | ✅ In repo |

### _docs/Version Control/
| File | Status |
|---|---|
| `SOURCE-CHANGELOGS.md` | ✅ In repo |
| `SCRIPTS-CHANGELOGS.md` | ✅ In repo |

---

## Navigation / infrastructure

| Item | Status | Notes |
|---|---|---|
| `navigation.py` — complete ITEM_ORDER | ✅ Delivered | `navigation_final.py` covers all 41 files — apply and run validate_docs.py |
| `validate_docs.py` | ✅ Works | Auto-generates nav from directory + ITEM_ORDER |
| `_config.yml` nav | ✅ Auto-generated | Never edit manually — validate_docs.py writes it |
| Toolbar links | ✅ Working | Slug-only URLs (`/docs/slug/`) resolve correctly |
| In-doc hyperlinks | ⚠️ Semi-working | Wrong directory prefix added by fix_links_v2.py — `revert_links.py` delivered to fix; someone is handling |
| `README.md` in Northbound | ⚠️ Delete | validate_docs.py skips README.md — `overview.md` is the correct file |
| Jekyll `section` layout | ❌ Not implemented | Needed for overview.md pages to render child page cards |
| Search | ❌ Not wired up | `search-index.json` exists in repo root — needs lunr.js or Algolia |
| Deployment to anylog.network/docs | ❌ Not done | DNS + GitHub Pages custom domain config |
| 404 page | ❌ Not done | Custom 404.html |
| SEO / Open Graph meta tags | ❌ Not done | For social sharing and search indexing |

---

## Content duplication to clean up

| Overlap | Fix |
|---|---|
| `AnyLog-CLI.md` and `get-cmds.md` both cover `get status`, `get processes`, `get connections` | Trim those from `AnyLog-CLI.md` — CLI page should focus on prompt, scripting, and `run client` only |
| `blockchain.md` and `policies-and-metadata.md` both cover policy types and blockchain commands | `blockchain.md` = command reference; `policies-and-metadata.md` = concepts/structure — remove command tables from the latter |
| Northbound `overview.md` and leftover `README.md` | Delete `README.md` |

---

## What is still missing

### Not yet written — high priority
| Missing doc | Notes |
|---|---|
| **Multi-node network setup** | Step-by-step: master + operator + query, connect nodes, send data, run a query. Old: `examples/Connecting Nodes.md`. Most important gap for new users. |
| **Master node setup** | Configuring and running a metadata master. Old: `master node.md`. Referenced heavily by existing docs. |
| **EdgeX integration** | Southbound connector example. Old: `using edgex.md`. |
| **policies-and-metadata.md** | Written — just needs to be committed to repo under `Network & Services/`. |
| **Security / Authentication** | SSL certs, user auth, API keys, node encryption. Old: `authentication.md`, `secure network.md`. **Being rewritten — skip for now.** |

### Not yet written — medium priority
| Missing doc | Notes |
|---|---|
| **Kubernetes deployment** | Helm chart, volumes, values.yaml. Old: `deployments/deploying_node.md` Kubernetes section. |
| **Upgrading AnyLog** | Docker pull, K8s rolling update, service restart without data loss. |
| **Directory structure** | AnyLog root layout (`anylog/`, `blockchain/`, `data/`, `archive/`). Old: `getting started.md` directory section. |
| **Configuration policies** | Storing node config as a blockchain policy for self-configuring nodes. Old: `training/advanced/Config Policies.md`. |
| **Profiling & monitoring queries** | `set query log`, `get query log`, slow query identification. Old: `profiling and monitoring queries.md`. |
| **Node monitoring scripts** | Integration with `deployment-scripts/southbound-monitoring`. Blocked — need script content shared. |
| **Mapping data to tables** (expanded) | File naming convention, tsd_info, time file commands. Old: `mapping data to tables.md`, `managing data files status.md`. |
| **Logging** | Event log, error log, query log — enabling, viewing, managing. Old: `logging events.md`. |

### Northbound connector stubs — need content
| File | What's needed |
|---|---|
| `PowerBI.md` | Step-by-step Web connector setup with screenshots |
| `Qlik.md` | REST connector setup for Qlik Sense/View |
| `Google.md` | OAuth setup, exporting results to Google Sheets |
| `postgres-connector.md` | PostgreSQL pass-through connector setup |
| `notification.md` | Slack webhook and generic HTTP POST alert setup |

### Low priority
| Missing doc | Notes |
|---|---|
| **NGINX as reverse proxy** | After security rewrite |
| **Nebula overlay network** | After security rewrite |
| **OSIsoft PI** | Niche — old: `registering pi in the anylog network.md` |
| **Scheduled pull** | Old: `scheduled pull.md` |
| **Tableau** | Referenced in old docs but no dedicated page |

---

## Slide decks used as source material

| Deck | Used for | Status |
|---|---|---|
| AnyLog Training | `getting-started.md` | ✅ Incorporated |
| Technical Training | `installing-anylog.md` | ✅ Incorporated |
| Deployment Scripts | `deployment-scripts.md` | ✅ Incorporated |
| Remote GUI | `remote-gui.md` | ✅ Incorporated |
| Data Generator & Data Mapping | `live-data-generator.md`, `data-ingestion.md` | ✅ Incorporated |

---

## Suggested next steps

### Immediate
1. Apply `navigation_final.py` → rename to `navigation.py` → run `validate_docs.py`
~~2. Delete `Querying Data (Northbound)/README.md`~~
3. Fix remaining hyperlink issues (`revert_links.py --write`)
4. Commit `policies-and-metadata.md` to `_docs/Network & Services/`

### High priority content
~~5. Write `edgex.md`~~
6. Write master node setup page
7. Write multi-node network setup example

### Infrastructure
~~8. Implement Jekyll `section` layout for `overview.md` pages (child page cards)~~
~~9. Wire up search (`search-index.json` → lunr.js)~~
10. Security docs — wait for designated person
11. Custom 404 page
12. Deploy to anylog.network/docs — DNS + GitHub Pages config

### Low priority
~~13. Fill out Northbound connector stubs (PowerBI, Qlik, Google, Postgres, Notifications)~~
14. Kubernetes deployment page
~~15. Configuration policies page~~
16. NGINX, Nebula — after security rewrite