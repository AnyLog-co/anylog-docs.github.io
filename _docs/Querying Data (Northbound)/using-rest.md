---
title: Using REST
description: Execute AnyLog commands and publish data over HTTP using GET, PUT, and POST.
layout: page
---
<!--
## Changelog
- 2026-04-17 | Created document
--> 

Any AnyLog node with the [REST service enabled](/docs/background-services/#rest-service) can receive commands and data over HTTP. This lets external applications, dashboards, and scripts interact with the network without running AnyLog themselves.

---

## HTTP method mapping

| Method | Used for |
|---|---|
| `GET` | Retrieve information — `sql`, `get`, `blockchain get`, `help` |
| `PUT` | Publish time-series data to a node |
| `POST` | All other commands — `set`, `reset`, `blockchain` operations, data via topic mapping |

### Common headers

| Header | Description |
|---|---|
| `User-Agent: AnyLog/1.23` | Required on every request |
| `command: [anylog command]` | The command to execute (GET and POST) |
| `destination: network` | Route a query across all relevant nodes (replaces `run client ()` on the CLI) |
| `destination: [IP:Port]` | Send to a specific node |

---

## GET requests

### Check node status
```bash
curl -X GET 'http://10.0.0.78:32349' \
  -H 'command: get status' \
  -H 'User-Agent: AnyLog/1.23'
```

### Get running processes
```bash
curl -X GET 'http://10.0.0.78:32349' \
  -H 'command: get processes' \
  -H 'User-Agent: AnyLog/1.23'
```

### Query metadata
```bash
curl -X GET 'http://10.0.0.78:32349' \
  -H 'command: blockchain get operator where company="AnyLog Co."' \
  -H 'User-Agent: AnyLog/1.23'
```

### SQL query across the network
```bash
curl -X GET 'http://10.0.0.78:32349' \
  -H 'command: sql mydb format=table "select * from rand_data where timestamp >= now() - 1 minute limit 10"' \
  -H 'User-Agent: AnyLog/1.23' \
  -H 'destination: network' \
  -w "\n"
```

> Always add `-w "\n"` to GET/SQL requests to avoid chunked-encoding display issues.

### Get help
```bash
curl -X GET 'http://10.0.0.78:32349' \
  -H 'command: help blockchain get' \
  -H 'User-Agent: AnyLog/1.23'
```

---

## POST requests

POST handles non-data commands and also data publishing via topic mapping.

### Reset the error log
```bash
curl -X POST 'http://10.0.0.78:32349' \
  -H 'User-Agent: AnyLog/1.23' \
  -H 'command: reset error log'
```

### Set a variable
```bash
curl -X POST 'http://10.0.0.78:32349' \
  -H 'User-Agent: AnyLog/1.23' \
  -H 'command: set company_name = AnyLog'
```

### Publish a blockchain policy
```bash
curl -X POST 'http://10.0.0.78:32349' \
  -H 'command: blockchain insert where policy = !new_policy and local = true and master = !master_node' \
  -H 'User-Agent: AnyLog/1.23'
```

### Publish data via topic (POST + msg client)

Before publishing data via POST, a `run msg client` with `broker=rest` must be active on the receiving node:

```anylog
<run msg client where broker = rest and port = !anylog_rest_port and user-agent = anylog and log = false and topic = (
  name = new_data and
  dbms = bring [dbms] and
  table = bring [table] and
  column.timestamp.timestamp = bring [timestamp] and
  column.value = (type = int and value = bring [value])
)>
```

Then publish:
```bash
curl -X POST 'http://10.0.0.78:32149' \
  -H 'command: data' \
  -H 'topic: new_data' \
  -H 'User-Agent: AnyLog/1.23' \
  -H 'Content-Type: text/plain' \
  --data-raw '[
    {"dbms": "mydb", "table": "sensor_data", "value": 50, "timestamp": "2019-10-14T17:22:13Z"},
    {"dbms": "mydb", "table": "sensor_data", "value": 55, "timestamp": "2019-10-14T17:22:14Z"}
  ]'
```

---

## PUT requests — publish data directly

PUT bypasses topic mapping. Data is sent with headers that directly specify the target database and table.

### Required headers

| Header | Description |
|---|---|
| `type: json` | Data format (default) |
| `dbms: [name]` | Target logical database |
| `table: [name]` | Target logical table |
| `mode: streaming` | Optional — buffer data instead of writing immediately |
| `User-Agent: AnyLog/1.23` | Required |

### Example

```bash
curl -X PUT 'http://10.0.0.78:32149' \
  -H 'type: json' \
  -H 'dbms: mydb' \
  -H 'table: sensor_data' \
  -H 'mode: streaming' \
  -H 'Content-Type: text/plain' \
  -H 'User-Agent: AnyLog/1.23' \
  -w "\n" \
  --data-raw '[
    {"device_name": "sensor-01", "value": 42.5, "timestamp": "2024-01-01T10:00:00Z"},
    {"device_name": "sensor-01", "value": 43.1, "timestamp": "2024-01-01T10:00:01Z"}
  ]'
```

Expected response: `{"AnyLog.status":"Success", "AnyLog.hash": "0dd6b959..."}`

---

## Sending commands to remote nodes

The `destination` header routes a command to a specific node or across the network:

```bash
# Send to a specific node
curl -X GET 'http://10.0.0.78:32349' \
  -H 'command: get operator' \
  -H 'User-Agent: AnyLog/1.23' \
  -H 'destination: 10.0.0.79:32148'

# Broadcast to all relevant nodes (SQL queries)
curl -X GET 'http://10.0.0.78:32349' \
  -H 'command: sql mydb format=table "select count(*) from rand_data"' \
  -H 'User-Agent: AnyLog/1.23' \
  -H 'destination: network' \
  -w "\n"
```

This is the REST equivalent of the CLI's `run client (IP:Port) command` and `run client () sql ...`.

---

## Enabling the REST service

If the REST service is not yet running on the target node:

```anylog
<run rest server where
  external_ip = [ip] and external_port = [port] and
  internal_ip = [local_ip] and internal_port = [local_port] and
  timeout = 0 and ssl = false and bind = false>
```

See [Background Services — REST service](/docs/background-services/#rest-service) for full options.