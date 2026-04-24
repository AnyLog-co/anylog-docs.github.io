---
title: Using REST
description: Execute AnyLog commands and publish data over HTTP using GET, PUT, and POST.
layout: page
---
<!--
## Changelog
- 2026-04-17 | Created document
- 2026-04-23 | Moved to Network and Services; added POST as GET alternative, AnyLog-Agent header, blockchain insert command, Python examples
-->

Any AnyLog node with the REST service enabled, can receive commands and data over HTTP. This lets external applications, dashboards, and scripts interact with the network without running AnyLog themselves.

---

## HTTP method mapping

| Method | Used for |
|---|---|
| `GET` | Retrieve information — `sql`, `get`, `blockchain get`, `help` |
| `POST` | All commands (alternative to GET) and data publishing via topic mapping |
| `PUT` | Publish time-series data directly to a node |

---

## Headers and the AnyLog-Agent

Every request requires an identity header. AnyLog accepts either `User-Agent` or `AnyLog-Agent`:

| Header | Value | Notes |
|---|---|---|
| `User-Agent: AnyLog/1.23` | Standard HTTP header | Works in server-side scripts (curl, Python `requests`, etc.) |
| `AnyLog-Agent: AnyLog/1.23` | Custom AnyLog header | **Preferred when calling from a browser** — avoids CORS preflight (see below) |

Both are accepted by the node and treated identically. For server-side code either works. For browser-based clients, use `AnyLog-Agent`.

### Why AnyLog-Agent for browser clients

Browsers treat `User-Agent` as a reserved header — `fetch()` cannot set it manually, and its presence in a cross-origin request triggers a CORS preflight (`OPTIONS`) that AnyLog nodes are not configured to answer. `AnyLog-Agent` is a custom header that both the browser and the node control explicitly, allowing the node to whitelist it:

```
Access-Control-Allow-Headers: AnyLog-Agent, Content-Type
```

See [Network and Services — REST service](/docs/network-services/#rest-service) and the [MCP-Examples CORS guide](https://github.com/AnyLog-co/MCP-Examples) for proxy-based solutions when direct browser access is not possible.

---

## GET requests

GET passes the command and options as HTTP headers.

### Common GET headers

| Header | Description |
|---|---|
| `command: [anylog command]` | The command to execute |
| `User-Agent: AnyLog/1.23` | Required (or `AnyLog-Agent: AnyLog/1.23`) |
| `destination: network` | Route a query across all relevant nodes |
| `destination: [IP:Port]` | Send to a specific node |

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

POST can be used as a direct alternative to GET, and is also the method for data publishing via topic mapping.

### POST as an alternative to GET

When using POST instead of GET, the headers used in GET become keys in the JSON body. This makes POST the natural choice for browser-based clients and any environment where setting custom HTTP headers is restricted.

**GET style:**
```bash
curl -X GET 'http://10.0.0.78:32349' \
  -H 'command: get status' \
  -H 'User-Agent: AnyLog/1.23'
```

**Equivalent POST style:**
```bash
curl -X POST 'http://10.0.0.78:32349' \
  -H 'Content-Type: application/json' \
  -d '{"command": "get status", "AnyLog-Agent": "AnyLog/1.23"}'
```

Both return the same response. Use `AnyLog-Agent` in the body when calling from a browser.

### Examples

#### Check node status
```bash
curl -X POST 'http://10.0.0.78:32349' \
  -H 'Content-Type: application/json' \
  -d '{"command": "get status where format=json", "AnyLog-Agent": "AnyLog/1.23"}' \
  -w "\n"
```

#### SQL query across the network
```bash
curl -X POST 'http://10.0.0.78:32349' \
  -H 'Content-Type: application/json' \
  -d '{
    "command": "sql mydb format=json:list and stat=false select * from rand_data where timestamp >= now() - 1 minute limit 10",
    "AnyLog-Agent": "AnyLog/1.23",
    "destination": "network"
  }' \
  -w "\n"
```

#### Reset the error log
```bash
curl -X POST 'http://10.0.0.78:32349' \
  -H 'Content-Type: application/json' \
  -d '{"command": "reset error log", "AnyLog-Agent": "AnyLog/1.23"}'
```

#### Set a variable
```bash
curl -X POST 'http://10.0.0.78:32349' \
  -H 'Content-Type: application/json' \
  -d '{"command": "set company_name = AnyLog", "AnyLog-Agent": "AnyLog/1.23"}'
```

### Publish a mapping policy to the blockchain

Before publishing data via POST topic mapping, a mapping policy must exist on the blockchain. Use `blockchain insert` to add it:

```bash
curl -X POST 'http://10.0.0.78:32349' \
  -H 'Content-Type: application/json' \
  -d '{
    "command": "blockchain insert where policy=!new_policy and local=true and master=!ledger_conn",
    "AnyLog-Agent": "AnyLog/1.23"
  }'
```

> The `master=!ledger_conn` parameter is optional — include it to also publish the policy to a master ledger node.

**Python example:**

```python
import json
import requests

def publish_policy(conn: str, ledger_conn: str, policy: dict, auth: tuple = (), timeout: int = 30) -> bool:
    headers = {
        'command': f'blockchain insert where policy=!new_policy and local=true and master={ledger_conn}',
        'User-Agent': 'AnyLog/1.23',
    }

    raw_policy = "<new_policy=%s>" % json.dumps(policy)

    try:
        r = requests.post(url='http://%s' % conn, headers=headers, data=raw_policy, auth=auth, timeout=timeout)
    except Exception as e:
        print('Failed to POST policy against %s (Error: %s)' % (conn, e))
        return False

    if int(r.status_code) != 200:
        print('Failed to POST policy against %s (Network Error: %s)' % (conn, r.status_code))
        return False

    return True
```

### Publish data via POST topic mapping

POST data publishing requires a `run msg client` with `broker=rest` active on the receiving node. This maps incoming JSON fields to a target database and table.

**Step 1 — configure the msg client on the node:**

```anylog
<run msg client where broker = rest and port = !anylog_rest_port and user-agent = anylog and log = false and topic = (
  name = new_data and
  dbms = "bring [dbms]" and
  table = "bring [table]" and
  column.timestamp.timestamp = "bring [timestamp]" and
  column.value = (type = int and value = "bring [value]")
)>
```

**Step 2 — publish data:**

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

**Python example:**

```python
import requests

def post_data(conn: str, topic: str, payload: str, auth: tuple = (), timeout: int = 30) -> bool:
    """
    Publish data via POST topic mapping.
    Requires a msg client with broker=rest running on the target node.

    Sample payload:
        [{"dbms": "mydb", "table": "sensor_data", "timestamp": "2021-10-20T15:35:49Z", "value": 3.14}]
    """
    headers = {
        'command': 'data',
        'topic': topic,
        'User-Agent': 'AnyLog/1.23',
        'Content-Type': 'text/plain'
    }

    try:
        r = requests.post('http://%s' % conn, auth=auth, timeout=timeout, headers=headers, data=payload)
    except Exception as e:
        print('Failed to send data via POST against %s (Error: %s)' % (conn, e))
        return False

    if int(r.status_code) != 200:
        print('Failed to send data via POST against %s (Network Error: %s)' % (conn, r.status_code))
        return False

    return True
```

---

## PUT requests — publish data directly

PUT bypasses topic mapping entirely. The target database and table are specified directly in the request headers, and data is written to the node immediately (or buffered in streaming mode).

### Required headers

| Header | Description |
|---|---|
| `type: json` | Data format (default) |
| `dbms: [name]` | Target logical database |
| `table: [name]` | Target logical table |
| `mode: streaming` | Optional — buffer data instead of writing immediately |
| `User-Agent: AnyLog/1.23` | Required (or `AnyLog-Agent: AnyLog/1.23`) |
| `Content-Type: text/plain` | Required |

### curl example

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

### Python example

```python
import json
import requests

def put_data(conn: str, dbms: str, table: str, payload, auth: tuple = (), mode: str = 'streaming', timeout: int = 30) -> bool:
    """
    Publish data directly via PUT — no topic mapping required.

    Args:
        conn:    IP:Port of the target node
        dbms:    logical database name
        table:   table name
        payload: list of dicts or JSON string
        mode:    'streaming' (buffered) or 'file' (immediate write)
    """
    headers = {
        'type': 'json',
        'dbms': dbms,
        'table': table,
        'mode': mode,
        'Content-Type': 'text/plain',
        'User-Agent': 'AnyLog/1.23'
    }

    if isinstance(payload, (dict, list)):
        try:
            payload = json.dumps(payload)
        except Exception as e:
            print('Failed to serialize payload (Error: %s)' % e)
            return False

    try:
        r = requests.put('http://%s' % conn, auth=auth, timeout=timeout, headers=headers, data=payload)
    except Exception as e:
        print('Failed to send data via PUT against %s (Error: %s)' % (conn, e))
        return False

    if int(r.status_code) != 200:
        print('Failed to send data via PUT against %s (Network Error: %s)' % (conn, r.status_code))
        return False

    return True
```

---

## Sending commands to remote nodes

The `destination` header (GET) or body key (POST) routes a command to a specific node or across the network:

```bash
# GET — send to a specific node
curl -X GET 'http://10.0.0.78:32349' \
  -H 'command: get operator' \
  -H 'User-Agent: AnyLog/1.23' \
  -H 'destination: 10.0.0.79:32148'

# GET — broadcast SQL to all relevant nodes
curl -X GET 'http://10.0.0.78:32349' \
  -H 'command: sql mydb format=table "select count(*) from rand_data"' \
  -H 'User-Agent: AnyLog/1.23' \
  -H 'destination: network' \
  -w "\n"

# POST equivalent — broadcast SQL to all relevant nodes
curl -X POST 'http://10.0.0.78:32349' \
  -H 'Content-Type: application/json' \
  -d '{
    "command": "sql mydb format=json:list and stat=false select count(*) from rand_data",
    "AnyLog-Agent": "AnyLog/1.23",
    "destination": "network"
  }' \
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