---
title: Introduction to AnyLog
description: Understanding AnyLog's architecture, node types, and core concepts.
layout: page
---

## What is AnyLog?

AnyLog turns many independent (industrial) databases into a single logical data network. Applications query a single node and the system automatically locates and retrieves data from wherever it resides across the network.

**EdgeLake** is the open-source version of AnyLog, distributed by the Linux Foundation. It provides most — but not all — of AnyLog's functionality.

> For installation and deployment instructions, see the [Installing & Deploying AnyLog](https://docs.google.com/presentation/d/1X8hMqmfAlUWNA1V3mqQe0Hi1x82m4vgB6Ai0k-boZdI/edit) guide.

---

## EdgeLake vs AnyLog

| Feature | EdgeLake | AnyLog |
|---|---|---|
| Cost | Free / Open-Source | Subscription |
| Virtual edge layer | ✅ | ✅ |
| Rule engine | ✅ | ✅ |
| Policy-based data management | ✅ | ✅ |
| Node management | ✅ | ✅ |
| Unified APIs, CLIs, Admin UI | ✅ | ✅ |
| Supported IoT connectors | ✅ | ✅ |
| Blockchain abstraction | ✅ | ✅ |
| MCP Integration | ✅ | ✅ |
| Aggregations | ❌ | ✅ |
| Automated Unified Namespace (UNS) | ❌ | ✅ |
| Security protocol & High Availability (HA) | ❌ | ✅ |

---

## Key Terminology

| Term | Definition |
|---|---|
| **Southbound** | Data flowing *in* from devices and sensors, stored into AnyLog |
| **Northbound** | Queries and results flowing *out* to applications |
| **Blockchain** | The metadata layer — tracks nodes, datasets, and configurations across the network |
| **Metadata** | Descriptive information about the data and nodes in the network (not the data itself) |
| **Services** | Components of AnyLog / EdgeLake that can be started and stopped independently |
| **Nodes / Agents** | Running AnyLog instances |
| **Containers** | Docker instances running AnyLog |

---

## Node Types

AnyLog uses a single base source code and configuration files. With the exception of Operator and Publisher nodes, any AnyLog agent can run any combination of services.

### Master Node (Blockchain Emulator)

Stores a copy of the network's metadata in a logical database rather than flat files. Systems can replace this node with an actual blockchain if needed.

- **Access:** Must be reachable by all nodes in the network
- **Location:** Cloud or office machine with consistent connectivity

### Operator Node

Dedicated to storing SQL and NoSQL data — these are the actual databases of the network. Usually deployed at the edge, with optional cloud backups for HA.

- **Access:** Must communicate bi-directionally with the master node, query node, and other operators in its cluster
- **Location:** At the edge; HA replica in the cloud

**Cluster:** An abstract policy that groups metadata within one or more operator nodes. This grouping allows query nodes to know exactly where to route requests to retrieve the relevant data. In a high-availability configuration, multiple operators share a cluster.

### Query Node

Accepts queries (typically via REST API) from applications and users. Uses blockchain metadata to determine which operator nodes hold the requested data, fans out the query, collects results, and returns them to the caller.

- **Access:** Must have network access to all operator nodes; individual users may run their own local query node with scoped access
- **Location:** Same network considerations as the master node

### Publisher Node *(AnyLog only)*

An optional edge node that accepts data from multiple sensors or devices and distributes it across the appropriate operator nodes. Used when a single ingestion point needs to fan data out to different clusters.

- **Access:** Must be able to reach the target operator node(s)
- **Location:** At the edge, alongside or near the data sources

---

## Network Architecture

### Data Flow Overview

The diagram below represents the logical flow of data and metadata across an AnyLog network.

```
  [ Sensor / Device ]
         │
         ▼
  [ Publisher Node ]  (optional — distributes data across operators)
         │
    ┌────┴────┐
    ▼         ▼
[ Operator ] [ Operator ]   ←──── [ Master Node / Blockchain Emulator ]
    ▲         ▲                         (metadata sync, dotted lines)
    └────┬────┘
         │
  [ Query Node ]
         │
         ▼
  [ User Application ]
```

**Roles at a glance:**

- The **Master Node** holds metadata for the entire network. Metadata is auto-generated as data arrives (node policies, table definitions, cluster mappings).
- The **Publisher Node** (optional) accepts raw sensor data and routes it to the correct operator nodes.
- **Operator Nodes** store the actual data. Together they form a virtual data lake.
- The **Query Node** receives requests from applications, uses metadata from the blockchain to locate the data, and assembles the final result.

### Traditional vs AnyLog Approach

**Traditional approach:**
Data travels from sensors → edge hardware → cloud before it is accessible to applications. "Real-time" dashboards often carry a significant hidden delay. Accessing edge data typically requires proprietary software tightly coupled to specific devices.

**With AnyLog / EdgeLake:**
Each edge data server becomes an operator node, directly part of the queryable network. Multiple operator nodes together form a virtual data lake. Applications connect to a single query node — not to each data source individually — and AnyLog handles locating and retrieving the data using blockchain metadata. This removes the complexity of managing multiple connections, eliminates the need to know where data physically resides, and dramatically reduces latency.

### Application-Facing Architecture

A typical deployment seen by an application looks like this:

```
  [ Customer Application ]
           │
           ▼
    [ Query Node ]
     /     |      \
    ▼      ▼       ▼
[Edge  ] [Edge  ] [Cloud /
 Op. I]  Op. II]  Historical Op.]
```

The application connects only to the query node. AnyLog routes each request to the appropriate operator(s) automatically, returning a unified result regardless of how many nodes or locations are involved.

---

## The Blockchain Layer

AnyLog uses a blockchain as a non-mutable ledger of metadata transactions across the peer-to-peer network.

**Key points:**

- **Data is not stored on the blockchain.** Raw data lives on operator nodes. The blockchain stores only metadata — node policies, table definitions, cluster assignments, and similar configuration records.
- Because the ledger is non-mutable, it ensures trust and consistency among all participants without a single point of failure.
- Operator, query, and publisher nodes synchronize their configurations via the blockchain, so the network self-organizes as nodes join or leave.

---

## How Data is Collected (Southbound)

| Method | Description |
|---|---|
| **REST PUT** | AnyLog maps the request to a DB, table, and key/value pairs |
| **REST POST** | AnyLog consumes messages and applies mapping to DB tables |
| **Remote Message Broker** | Kafka / MQTT — AnyLog subscribes and applies mapping to DB tables |
| **Local Message Broker** | AnyLog itself acts as the MQTT broker |
| **OPC-UA / EtherIP** | Values stored in timestamp/value format for time-series data |
| **gRPC** | Used for KubeArmor, monitoring tools, and video/inference streaming |

The mapping layer ensures all incoming messages or streams are translated into the correct database structure so data is immediately queryable.

AnyLog supports a **Universal Namespace (UNS)** — either built-in or customer-defined — providing consistent variable names across all nodes. EdgeLake does not include a built-in UNS.

---

## How Querying Works

Querying across the network relies on two independent components:

**Part 1 — Metadata sync**
A background process continuously synchronizes metadata between the blockchain (emulator) and each node in the network, particularly query nodes. This keeps routing information current as the network changes.

**Part 2 — Query execution**

1. A user sends a `SELECT` request to the query node (typically via REST).
2. The query node uses its local copy of the blockchain metadata to identify which operator node(s) hold the relevant data.
3. The query node distributes the request. For aggregate queries (e.g. `SELECT avg(...)`), each operator computes partial results (`sum`, `count`) and returns them to the query node, which assembles the final answer.
4. The result is returned to the application.

This means applications never need to know where data is physically stored — that concern is fully handled by the AnyLog network.
