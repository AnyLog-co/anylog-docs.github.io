---
title: Deployment Scripts (Changelog)
description: Release history and notable changes for AnyLog deployment scripts.
layout: page
---

## Unreleased
<!-- last-processed: -->

<!-- Developers: add bullets below as changes land in your branch -->

---

## 2026

### [a73584e] · 2026-04-08 (latest)

| Date | Commit | Summary |
|------|--------|---------|
| 2026-04-08 | [a73584e] | Drone deployment scripts and bind/mode configuration |
|            |           | Debug and print improvements across deployment scripts |
|            |           | Policy sync and seed updates for node deployment |
|            |           | Aggregation script updates and mapping fixes |
|            |           | Missing parameter fixes across southbound connectors |
|            |           | Blockchain policy updates and debug additions |
|            |           | Deployment mode configuration (trying/false pattern cleanup) |

---

## 2025

2025 was defined by **policy maturity, monitoring expansion, and networking improvements**. The blockchain policy system was significantly extended with cluster, license, and relay policy support. Monitoring scripts were expanded across southbound connectors. Syslog integration was refined. Networking and overlay configuration scripts were added for multi-node deployments. Docker-based deployment was introduced for scripts. A major reorg consolidated script paths and naming conventions.

| Date | Commit | Summary |
|------|--------|---------|
| 2025-12 | — | Publish workflow scripts; relay and networking configs added |
|         |   | Cluster policy support in node-deployment |
|         |   | Monitoring script refactors for southbound connectors |
| 2025-09 | — | Blockchain policy reorg; path and config cleanup |
|         |   | Syslog script updates and parameter fixes |
| 2025-06 | — | License key management scripts added |
|         |   | Docker deployment support added to scripts |
| 2025-01 | — | License key integration — initial scripts |
|         |   | Monitoring improvements for industrial southbound |

---

## 2024

2024 focused on **smart city, gRPC/KubeArmor integration, and policy tooling**. Smart city demo scripts (power plant, waste water, water plant) were built out under the `customers/` directory. KubeArmor gRPC connector scripts were added and debugged. Policy creation and blockchain sync scripts were improved. Syslog ingestion scripts were introduced. Generic deployment configs were extended, and a set of demo and training scripts was organized.

| Date | Commit | Summary |
|------|--------|---------|
| 2024-12 | — | Generic deployment configs expanded; policy debug scripts added |
|         |   | Monitoring scripts updated with source and params fixes |
| 2024-09 | — | Smart city customer scripts — Grafana dashboards for power plant, waste water, water plant |
|         |   | Syslog ingestion scripts added |
| 2024-06 | — | gRPC / KubeArmor connector scripts added and debugged |
|         |   | Policy tooling improved — company/name fields, healthcheck |
| 2024-01 | [dcd5f17] | Fix KubeArmor integration |
|         | [62c40f7] | Added company and name fields to policy |
|         | [5b2e2bc] | gRPC script initial commit |
|         | [0cf02bf] | KubeArmor healthcheck |

---

## 2023

The `deployment-scripts` repository was established in May 2023. Initial work focused on **repository organization, operator/publisher policy scripts, and EdgeX connector support**. Branch structure was defined, core script paths were laid out, and monitoring and deployment scripts were created for standard AnyLog node roles. License policy scripts were introduced. Training scripts and sample configurations were added to help onboard new users.

| Date | Commit | Summary |
|------|--------|---------|
| 2023-12 | — | License policy scripts; monitoring scripts for operator nodes |
|         |   | Training and sample script additions |
| 2023-09 | — | Deployment script reorg; policy and config path standardization |
|         |   | Master node deployment scripts added |
| 2023-06 | [2ac9aee] | EdgeX connector scripts — initial commit |
|         | [45315b0] | EdgeX code additions |
| 2023-05 | [1938fba] | Initial commit — branch structure and repo organization |
|         | [d4e0bc9] | Reorg of script directories |
|         | [44ef282] | Rename and path additions |

---

*For the full commit-level history, run `git log` or browse the repository on GitHub.*