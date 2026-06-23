import json
import requests
import datetime

OPERATOR = 'http://10.0.0.69:32149'

# Publish data directly via PUT — no topic mapping or msg client required
payload = [
    {"device_name": "sensor-01", "value": 42.5, "timestamp": datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')},
    {"device_name": "sensor-01", "value": 43.1, "timestamp": (datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%S.%f')}
]

r = requests.put(
    url=OPERATOR,
    headers={
        'type': 'json',
        'dbms': 'mydb',
        'table': 'sensor_data',
        'mode': 'streaming',
        'Content-Type': 'text/plain',
        'User-Agent': 'AnyLog/1.23'
    },
    data=json.dumps(payload)
)
print(r.text)  # {"AnyLog.status":"Success", "AnyLog.hash": "..."}