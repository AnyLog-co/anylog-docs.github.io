---
title: Adding Data
description: All the ways to get data into AnyLog operator nodes — REST, MQTT, Kafka, watch directory, and more.
layout: page
---

AnyLog hosts data on **Operator nodes**. Any connected node can be configured to receive and store data. There are several ingestion methods, all feeding into the same underlying pipeline.

> For a higher-level overview of southbound services, see [Data Ingestion](/docs/data-ingestion/).

---

## Node roles for data ingestion

A node receiving data can be configured as either:

- **Operator** — stores incoming data directly in a local database
- **Publisher** — forwards each received file to one or more Operator nodes that manage the destination table

---

## Method 1 — Watch directory

The Watch Directory is a disk directory monitored by Operator nodes. Any JSON or SQL file placed there is automatically processed.

### Default processing flow

1. The file is read by the operator
2. Processing variables are derived from the file name (database, table, mapping policy)
3. If the logical table doesn't exist, it is created automatically
4. The file data is inserted into the table

### File naming convention

```
[dbms name].[table name].[data source].[hash value].[instructions].json
```

Display the structure dynamically:
```anylog
show json file structure
```

| Segment | Required | Description |
|---|---|---|
| `dbms name` | ✅ | Logical database to contain the data |
| `table name` | ✅ | Logical table to contain the data |
| `data source` | optional | Unique ID for the data source (e.g. sensor ID) |
| `hash value` | optional | Hash identifying the file |
| `instructions` | optional | ID of a mapping policy for this file's data |

Get the hash value of a file:
```anylog
file hash [file name and path]
```

### JSON data format

Instances must be newline-delimited JSON:
```json
{"parentelement": "62e71893", "device_name": "ADVA FSP3000R7", "value": 0, "timestamp": "2019-10-11T17:05:08Z"}
{"parentelement": "68ae8bef", "device_name": "Catalyst 3500XL", "value": 50, "timestamp": "2019-10-14T17:22:13Z"}
```

---

## Method 2 — REST API (PUT)

Send data directly to a node via HTTP PUT. The node maps request headers to a target database and table.

### Required headers

| Key | Value |
|---|---|
| `User-Agent` | `AnyLog/1.23` |
| `type` | Data type (default: `json`) |
| `dbms` | Logical database name |
| `table` | Logical table name |
| `mode` | `file` (default) or `streaming` |
| `source` | Optional unique data source ID |
| `instructions` | Optional mapping policy ID |

### Example

```bash
curl --location --request PUT '10.0.0.226:32149' \
  --header 'type: json' \
  --header 'dbms: test' \
  --header 'table: table1' \
  --header 'Content-Type: text/plain' \
  --header 'User-Agent: AnyLog/1.23' \
  -w "\n" \
  --data-raw '[
    {"device_name": "ADVA FSP3000R7", "value": 0, "timestamp": "2019-10-11T17:05:08Z"},
    {"device_name": "Catalyst 3500XL", "value": 50, "timestamp": "2019-10-14T17:22:13Z"}
  ]'
```

Expected response: `{"AnyLog.status":"Success", "AnyLog.hash": "0dd6b959..."}`

---

## Method 3 — REST API (POST)

POST sends data through the message client mapping layer. The `topic` header determines how data is mapped to a table.

### Prerequisites

A `run msg client` command must be active on the receiving node with a matching topic. Example:

```
<run msg client where broker=rest and port=!anylog_rest_port and user-agent=anylog and log=false and topic=(
  name=new_data and
  dbms=bring [dbms] and
  table=bring [table] and
  column.timestamp.timestamp=bring [timestamp] and
  column.value=(type=int and value=bring [value])
)>
```

### cURL example

```bash
curl --location --request POST '10.0.0.226:32149' \
  --header 'command: data' \
  --header 'topic: new_data' \
  --header 'User-Agent: AnyLog/1.23' \
  --header 'Content-Type: text/plain' \
  --data-raw '[
    {"dbms": "aiops", "table": "fic11", "value": 50, "timestamp": "2019-10-14T17:22:13Z"},
    {"dbms": "aiops", "table": "fic16", "value": 501, "timestamp": "2019-10-14T17:22:13Z"}
  ]'
```

### Python example

```python
import json, requests

conn = '192.168.50.159:2051'
headers = {
    'command': 'data',
    'topic': 'new_data',
    'User-Agent': 'AnyLog/1.23',
    'Content-Type': 'text/plain'
}
data = [
    {"dbms": "aiops", "table": "fic11", "value": 50, "timestamp": "2019-10-14T17:22:13Z"},
]
r = requests.post('http://%s' % conn, headers=headers, data=json.dumps(data))
```

---

## Method 4 — Third-party message broker (MQTT / Kafka)

AnyLog subscribes to an external broker and maps received messages to database tables.

See [Data Ingestion — run msg client](/docs/data-ingestion/#run-msg-client) for full details.

Validate status:
```anylog
get msg client
```

---

## Method 5 — AnyLog as a local broker

Configure AnyLog itself as an MQTT broker so clients can publish directly to it.

Validate broker status:
```anylog
get broker
get msg client
```

---

## File mode vs streaming mode

| Mode | Behaviour | Best for |
|---|---|---|
| `file` (default) | Each PUT request is a self-contained file, registered and processed independently | Large payloads, infrequent data |
| `streaming` | Data is buffered internally and flushed when a time or volume threshold is hit | High-frequency, low-volume readings |

Set mode via the `mode` header in a PUT request, or configure thresholds:

```anylog
set buffer threshold where time = 1 hour and volume = 2KB
```

Full options:

| Option | Default | Description |
|---|---|---|
| `dbms_name` | All databases | Target database |
| `table_name` | All tables | Target table |
| `time` | 60 seconds | Time threshold to flush |
| `volume` | 10KB | Volume threshold to flush |
| `write_immediate` | false | Write to local DB immediately, independent of flush |

Enable the streamer process:
```anylog
run streamer
```

Check streaming status:
```anylog
get streaming
```

---

## Southbound connectors — flow diagram

```
Option A: External MQTT/Kafka broker  →  AnyLog Broker Client  ─┐
Option B: AnyLog as local broker      →  AnyLog Broker Client  ─┤
Option C: REST POST                   →  Client Data Mapper     ─┤
                                                                  ▼
Option D: REST PUT (no mapping)       ──────────────────────►  Data Buffers  →  DBMS Update
                                                                  ▲
Option E: JSON files in watch dir     ──────────────────────►  JSON Files    →  DBMS Update
Option F: SQL files in watch dir      ──────────────────────►  SQL Files     →  DBMS Update
```

---

## Monitoring commands

| Command | Description |
|---|---|
| `get msg client` | Status of message client mapping (MQTT/Kafka/POST) |
| `get broker` | Status of the local AnyLog broker |
| `get rest calls` | Status of HTTP PUT/POST calls |
| `get streaming` | Status of internal streaming buffers |
| `get operator` | Status of file processing (watch directory) |