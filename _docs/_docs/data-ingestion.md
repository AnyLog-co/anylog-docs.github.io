---
title: Data Ingestion
description: How to get data into AnyLog using REST, MQTT, Kafka, OPC-UA, and gRPC.
layout: page
---

## Southbound services overview

AnyLog supports multiple data ingestion methods. All incoming data — regardless of source — passes through a mapping layer that translates it into the correct database structure, making it immediately queryable.

| Method | Description |
|---|---|
| **REST PUT** | AnyLog maps the request directly to a database, table, and key/value pairs |
| **REST POST** | AnyLog consumes messages and applies mapping to database tables |
| **Remote Message Broker** | Kafka or MQTT — AnyLog subscribes and applies mapping to DB tables |
| **Local Message Broker** | AnyLog acts as the MQTT broker itself |
| **OPC-UA / EtherIP** | Values stored in timestamp/value format for time-series applications |
| **gRPC** | Used for KubeArmor, monitoring tools, and video/inference streaming |

AnyLog supports a **Universal Namespace (UNS)** — either built-in or customer-defined — providing consistent variable names across all nodes. Note that EdgeLake does not include a built-in UNS.

---

## Data path

Data reaches operator nodes either directly (via a supported southbound service) or through an intermediary:

```
[ Sensor / Device ]
        │
  ┌─────┴──────────────────────────────────┐
  │ Direct                                  │ Via Publisher
  ▼                                         ▼
[ Operator Node ] ←──── [ AnyLog Publisher Node ]
                                  ▲
                         (fans data across
                          multiple operators)
```

A **publisher node** is an optional AnyLog edge node that accepts data from sensors and automatically routes it to the appropriate operator nodes. It is used when:
- Data from a single ingestion point needs to be split across different clusters
- The sensor or device cannot directly reach the operator nodes due to network topology

In parallel, a **query node** can always be used to retrieve data and metadata from operator nodes for use by customer applications.

---

## REST PUT

The simplest ingestion method. AnyLog maps the HTTP headers to a target database and table, and the body is parsed as key/value pairs.

```bash
curl -X PUT "http://127.0.0.1:32149" \
  -H "type: json" \
  -H "dbms: mydb" \
  -H "table: rand_data" \
  -H "mode: streaming" \
  -H "Content-Type: text/plain" \
  --data '[
    {"timestamp":"2026-03-12T10:00:00Z","value":12.5},
    {"timestamp":"2026-03-12T10:00:01Z","value":18.2},
    {"timestamp":"2026-03-12T10:00:02Z","value":9.7}
  ]'
```

Expected response: `{"AnyLog.status":"Success", "AnyLog.hash": "0"}`

---

## REST POST

Used when data is published through the message client mapping layer (see [`run msg client`](/docs/msg-client/) below). The POST goes to the operator's REST port with a topic header instead of direct table/database headers.

```bash
curl -X POST "http://127.0.0.1:32149" \
  -H "command: data" \
  -H "topic: my-data" \
  -H "User-Agent: AnyLog/1.23" \
  -H "Content-Type: text/plain" \
  -d '[
    {"dbms":"mydb","table":"rand_data","timestamp":"2026-04-03 18:31:10.125431","value":12.48},
    {"dbms":"mydb","table":"rand_data","timestamp":"2026-04-03 18:31:10.625812","value":87.29}
  ]'
```

---

## The message broker / client relationship

When data arrives via MQTT, Kafka, or REST POST, AnyLog uses two components:

**Part 1 — Message broker:** Decides where messages come from.
- **Local broker:** AnyLog itself acts as the MQTT broker. The node must have the broker service enabled.
- **Remote broker:** An external broker (e.g. Mosquitto, Kafka). AnyLog connects as a consumer.

**Part 2 — Message client (`run msg client`):** Connects to the broker and maps incoming content to the correct database and table structure.

> Unlike generic message brokers, AnyLog instances cannot connect to one another's MQTT broker to pull messages. Only the message client service bridges that gap.

---

## `run msg client`

The `run msg client` command starts the mapping service that subscribes to a topic and routes data into storage.

### Parameter reference

| Section | Parameter | Description |
|---|---|---|
| **Connection** | `broker` | IP address, `local` (AnyLog broker), or `rest` (for REST POST) |
| | `port` | Port associated with the broker |
| **Auth** *(optional)* | `user` | Username for remote broker |
| | `password` | Password for the user above |
| | `user-agent` | Set to `anylog` — required only for REST POST |
| | `log` | `true` / `false` — write events to screen |
| **Routing** | `name` | Broker topic to subscribe to |
| | `dbms` | Target logical database — hardcoded or from payload |
| | `table` | Target table — hardcoded or from payload |
| **Schema** | `column.timestamp.timestamp` | Use `"bring [field]"` to pull from payload, or `now()` for ingestion time |
| | `column.[name]` | Any non-timestamp column: set `type` and `value` to map from a payload key |

### Full syntax

```
<run msg client where
  broker    = [IP | local | rest] and
  port      = [PORT] and
  user      = [USERNAME] and       # optional
  password  = [PASSWORD] and       # optional
  log       = [true | false] and
  user-agent= anylog and           # REST POST only
  topic = (
    name    = [TOPIC] and
    dbms    = [DB NAME] and
    table   = [TABLE NAME] and
    column.timestamp.timestamp = "bring [field]" | now() and
    column.[col_name] = (
      type  = [float | int | bool | str] and
      value = "bring [PAYLOAD KEY]"
    )
  )>
```

### Example — local MQTT broker

```
<run msg client where
  broker = local and
  port   = 32150 and
  log    = false and
  topic  = (
    name  = my-data and
    dbms  = mydb and
    table = rand_data and
    column.timestamp.timestamp = "bring [timestamp]" and
    column.value = (
      type  = float and
      value = "bring [value]"
    )
  )>
```

### Example — REST POST client

```
<run msg client where
  broker     = rest and
  port       = 32149 and
  log        = false and
  user-agent = anylog and
  topic      = (
    name  = my-data and
    dbms  = mydb and
    table = rand_data and
    column.timestamp.timestamp = "bring [timestamp]" and
    column.value = (
      type  = float and
      value = "bring [value]"
    )
  )>
```

---

## Using a mapping policy

For more complex scenarios, the same mapping can be expressed as a **policy** stored on the blockchain. Policies offer:

- Easier reusability across nodes
- Better data type support (epoch timestamps, blob integration)
- Ability to split data across multiple tables

### Define the policy

```
<new_policy = {
  "mapping": {
    "id": "my-policy",
    "dbms": "mydb",
    "table": "rand_data",
    "schema": {
      "timestamp": {
        "type": "timestamp",
        "bring": "[timestamp]",
        "default": "now()"
      },
      "value": {
        "type": "float",
        "value": "[value]"
      }
    }
  }
}>
```

### Publish the policy to the blockchain

```
<blockchain insert where
  policy = !new_policy and
  local  = true and
  master = !ledger_conn>
```

### Reference the policy in `run msg client`

```
<run msg client where
  broker = local and
  log    = false and
  topic  = (
    name   = my-data and
    policy = my-policy
  )>
```

---

## Validating ingestion

### Check the message client is running

```bash
curl -X GET 127.0.0.1:32149 \
  -H "command: get msg client" \
  -H "User-Agent: AnyLog/1.23"
```

### Check streaming status

```bash
curl -X GET 127.0.0.1:32149 \
  -H "command: streaming" \
  -H "User-Agent: AnyLog/1.23"
```

### Query data back out

```bash
curl -X GET 127.0.0.1:32349 \
  -H "command: sql mydb format=table SELECT timestamp, value FROM rand_data WHERE period(minute, 1, now(), timestamp)" \
  -H "User-Agent: AnyLog/1.23" \
  -H "destination: network"
```

---

## Sample scripts

| Script | Description |
|---|---|
| [basic_msg_client.al](https://github.com/AnyLog-co/deployment-scripts/blob/main/sample-scripts/basic_msg_client.al) | Basic `run msg client` for MQTT — used when `ENABLE_MQTT=true` in configuration |
| [basic_kafka_client.al](https://github.com/AnyLog-co/deployment-scripts/blob/main/sample-scripts/basic_kafka_client.al) | Same as above but uses `run kafka consumer` instead of `run msg client` |
| [edgex.al](https://github.com/AnyLog-co/deployment-scripts/blob/main/sample-scripts/edgex.al) | Mapping policy example for the EdgeX retail-device1 demo (MQTT or REST POST) |
| [telegraf.al](https://github.com/AnyLog-co/deployment-scripts/blob/main/sample-scripts/telegraf.al) | Mapping policy example for data coming in via Telegraf |
| [fledge.al](https://github.com/AnyLog-co/deployment-scripts/blob/main/sample-scripts/fledge.al) | Multiple topics handled in a single `run msg client` |
