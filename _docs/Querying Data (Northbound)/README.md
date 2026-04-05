---
title: Northbound Examples
description: Query AnyLog from Postman and Python — practical examples for GET, PUT, and POST over REST.
layout: page
---

These examples show how to interact with AnyLog nodes from external tools and scripts. For the full REST API reference see [Using REST](/docs/using-rest/).

---

## Postman

[Download Postman](https://www.postman.com/downloads/)

### Without SSL

1. Open Postman and create a collection
2. Add a new **GET** request
3. Set the URL to `http://[node-ip]:[rest-port]`
4. Add headers:

| Key | Value |
|---|---|
| `User-Agent` | `AnyLog/1.23` |
| `command` | Your AnyLog command (e.g. `get status`) |

5. Click **Send**

### With SSL

1. Set the URL to `https://[node-ip]:[rest-port]`
2. Same headers as above
3. In **Settings**: disable "Enable SSL certificate verification"
4. In **Default Settings**: add the CA certificate (public key)
5. Add your client certificate and private key

> SSL certificate setup is described in the [Authentication](https://github.com/AnyLog-co/documentation/blob/master/authentication.md#using-ssl-certificates) section of the AnyLog documentation.

### Example queries in Postman

- `get status` — check node is running
- `get processes` — list active services
- `blockchain get operator` — list all operator nodes
- `sql mydb format=table "select * from rand_data limit 10"` — with `destination: network` header

---

## Python

### Simple GET query

```python
import requests

def get_data(
    conn: str = '10.0.0.78:32349',
    db_name: str = 'mydb',
    sql_cmd: str = "select increments(minute, 1, timestamp), min(timestamp) as ts, count(*) as row_count from ping_sensor where timestamp >= NOW() - 10 minutes"
) -> list:
    """
    Execute a SQL query against an AnyLog query node via REST GET.
    Returns the query result as a list of dicts.
    """
    headers = {
        "command": f"sql {db_name} format=json and stat=false {sql_cmd}",
        "User-Agent": "AnyLog/1.23",
        "destination": "network"
    }

    try:
        r = requests.get(url=f"http://{conn}", headers=headers)
    except Exception as e:
        print(f"Failed to connect to {conn}: {e}")
        return []

    if r.status_code != 200:
        print(f"Request failed: HTTP {r.status_code}")
        return []

    try:
        return r.json()['Query']
    except Exception:
        return r.text


if __name__ == '__main__':
    results = get_data()
    for row in results:
        print(row)
```

### With pandas and matplotlib

```python
import pandas as pd
import matplotlib.pyplot as plt
import requests

def get_data(conn='10.0.0.78:32349', db_name='mydb',
             sql_cmd="select increments(minute, 1, timestamp), min(timestamp) as ts, count(*) as row_count from ping_sensor where timestamp >= NOW() - 10 minutes"):
    headers = {
        "command": f"sql {db_name} format=json and stat=false {sql_cmd}",
        "User-Agent": "AnyLog/1.23",
        "destination": "network"
    }
    r = requests.get(url=f"http://{conn}", headers=headers)
    if r.status_code == 200:
        return r.json().get('Query', [])
    return []

results = get_data()
df = pd.DataFrame(results)
df['ts'] = pd.to_datetime(df['ts'])
df.set_index('ts', inplace=True)
df['row_count'].plot(title='Rows per minute')
plt.show()
```

### PUT — publish data

```python
import requests, json

conn = '10.0.0.78:32149'
headers = {
    'type': 'json',
    'dbms': 'mydb',
    'table': 'sensor_data',
    'mode': 'streaming',
    'Content-Type': 'text/plain',
    'User-Agent': 'AnyLog/1.23'
}
data = [
    {"timestamp": "2024-01-01T10:00:00Z", "value": 42.5, "device": "sensor-01"},
    {"timestamp": "2024-01-01T10:00:01Z", "value": 43.1, "device": "sensor-01"}
]

r = requests.put(f"http://{conn}", headers=headers, data=json.dumps(data))
print(r.json())  # {"AnyLog.status": "Success", "AnyLog.hash": "..."}
```

### POST — publish via topic

```python
import requests, json

conn = '10.0.0.78:32149'
headers = {
    'command': 'data',
    'topic': 'my-topic',
    'User-Agent': 'AnyLog/1.23',
    'Content-Type': 'text/plain'
}
data = [
    {"dbms": "mydb", "table": "sensor_data", "value": 50, "timestamp": "2024-01-01T10:00:00Z"},
    {"dbms": "mydb", "table": "sensor_data", "value": 55, "timestamp": "2024-01-01T10:00:01Z"}
]

r = requests.post(f"http://{conn}", headers=headers, data=json.dumps(data))
print(r.status_code)
```

> A `run msg client where broker=rest` with matching `topic` must be active on the operator. See [Data Ingestion](/docs/data-ingestion/#rest-post).