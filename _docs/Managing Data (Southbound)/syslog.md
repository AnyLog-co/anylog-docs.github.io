---
title: Syslog
description: Ingest BSD and IETF syslog messages from Linux, Mac, and network devices directly into AnyLog.
layout: page
---

AnyLog can act as a syslog receiver, accepting messages from any host that supports TCP syslog output. Rules map incoming messages to logical databases and tables.

---

## Syslog formats

### BSD (RFC 3164)
Fields: `Priority`, `Timestamp` (MMM dd hh:mm:ss), `Hostname`, `Tag` (process name + PID), `Message`

### IETF (RFC 5424)
Fields: `Priority`, `Version`, `Timestamp` (ISO 8601), `Hostname`, `Application`, `PID`, `Message ID`, `Structured Data`, `Message`

---

## Prerequisites

1. The AnyLog node must have the **message broker service** running — this is the TCP listener that receives syslog traffic:
   ```anylog
   run message broker where external_ip = !ip and external_port = !broker_port and threads = 3
   ```
   Check which port to direct syslog output to:
   ```anylog
   get connections
   ```

2. Configure the **syslog source** to use TCP and point to the AnyLog broker IP and port.

---

## Setting a syslog rule

Rules tell AnyLog how to route and parse incoming syslog data:

```anylog
set msg rule [rule name] if ip = [source IP] and port = [port] and header = [header text] then dbms = [dbms] and table = [table] and syslog = [true/false] and extend = ip and format = [format] and topic = [topic]
```

| Option | Required | Description |
|---|---|---|
| rule name | ✅ | Unique name for this rule |
| `ip` | — | Source IP to match. If omitted, matches all IPs |
| `port` | — | Source port to match. If omitted, matches all ports |
| `header` | — | Match messages with a specific prefix string |
| `dbms` | ✅ | Target logical database |
| `table` | ✅ | Target table |
| `syslog` | — | `true` — parse as BSD syslog (default column names). Use `format = IETF` for IETF format |
| `extend` | — | Add extra fields to the JSON. `extend = ip` adds the source IP |
| `format` | — | Override default format. Set to `IETF` for RFC 5424 |
| `topic` | — | Route data through the msg client mapping layer (like MQTT) |
| `structure` | — | `included` — the first message event describes the column structure |

> When `syslog = true`, column names are pre-determined by the format (BSD by default). When `syslog` is not set, use `structure = included` so the first event defines the schema.

---

## Examples

### Example 1 — BSD syslog from a specific host and port

```anylog
set msg rule my_rule if ip = 10.0.0.78 and port = 1468 then dbms = test and table = syslog and syslog = true
```

### Example 2 — Linux journalctl via netcat with a header prefix

Pipe journalctl output to AnyLog, prefixing each line with a custom header:

```bash
journalctl --since "${NOW}" | awk '{print "al.sl.header.new_company.syslog", $0}' | nc -w 1 73.202.142.172 7850
```

Rule on the operator that matches the prefix:

```anylog
set msg rule my_rule if ip = 139.162.126.241 and header = al.sl.header.new_company.syslog then dbms = test and table = syslog and syslog = true
```

### Example 3 — Mac syslog with dynamic structure from first event

Script:
```bash
(log show --info --start '2024-01-01 16:50:00' --end '2024-12-01 16:51:00' | awk '{print "al.sl", $0}') | nc -w 1 10.0.0.78 7850
```

The first event contains the column headers:
```
al.sl Timestamp                       Thread     Type        Activity             PID    TTL
al.sl 2024-01-01 17:51:35.253053-0800 0x4d0c71   Default     0x39223d             482    3   ...
```

Rule using `structure = included`:
```anylog
set msg rule my_rule if ip = 10.0.0.251 and header = al.sl then dbms = test and table = syslog_mac and structure = included
```

---

## Manage rules

```anylog
get msg rules              # list all rules
reset msg rule [rule name] # remove a rule
```

---

## Trace and debug

Enable trace to see the source IP, port, and first 100 bytes of each incoming message:

```anylog
trace level = 2 run message broker
```

Example output:
```
[Message Broker Received 1650 Bytes] [Source: 10.0.0.78:1468] [Data: <134>Jan 26 17:30:10 DESKTOP sshd[3268] User login...]
```

Monitor processed event counts with `get msg rules`.