import json
import requests
import datetime


OPERATOR  = 'http://10.0.0.69:32149'
QUERY     = 'http://10.0.0.69:32349'
HEADERS   = {'AnyLog-Agent': 'AnyLog/1.23'}


# 1. Define mapping policy
policy = {
    "mapping": {
        "id": "my-mapping1",
        "dbms": "bring [dbms]",
        "table": "bring [table]",
        "readings": "",
        "schema": {
            "timestamp": {"default": "now()", "type": "timestamp", "bring": "[timestamp]"},
            "value":     {"default": None,    "type": "float",     "bring": "[value]"}
        }
    }
}

# 2. Publish mapping policy to the blockchain
requests.post(
    url=OPERATOR,
    headers={**HEADERS, 'command': 'blockchain insert where policy=!new_policy and local=true and master_node=!ledger_conn'},
    data=f'<new_policy={json.dumps(policy)}>'
)

# 3. Start msg client on the operator node
requests.post(
    url=OPERATOR,
    headers={**HEADERS, 'command': 'run msg client where broker=rest and user-agent=anylog and log=false and topic=(name=my-topic and policy=my-mapping1)'}
)

# 4. Publish data — JSON keys are mapped via the policy
payload = [
    {"dbms": "mydb", "table": "sensor_data", "value": 50, "timestamp": datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')},
    {"dbms": "mydb", "table": "sensor_data", "value": 55, "timestamp": (datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%S.%f')}
]
requests.post(
    url=OPERATOR,
    headers={**HEADERS, 'command': 'data', 'topic': 'my-topic', 'Content-Type': 'text/plain'},
    data=json.dumps(payload)
)

# 5. Validate data is being received — check streaming status on operator via query node
r = requests.post(
    url=QUERY,
    headers={'Content-Type': 'application/json'},
    json={'command': 'get streaming', 'AnyLog-Agent': 'AnyLog/1.23', 'destination': '10.0.0.69:32148'}
)
print(r.text)

# 6. Query data via the query node
r = requests.post(
    url=QUERY,
    headers={'Content-Type': 'application/json'},
    json={
        'command': 'sql mydb format=json:list and stat=false select * from sensor_data where timestamp >= now() - 1 minute limit 10',
        'AnyLog-Agent': 'AnyLog/1.23',
        'destination': 'network'
    }
)
print(r.json())