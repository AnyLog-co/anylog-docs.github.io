---
title: Telegraf
description: How to utilize Telegraf with generic mapping policies 
layout: page
---
<!--
## Changelog
- 2026-04-17 | Created new document explaining mapping with the use of Telegraf
-->


# Telegraf

<a href="https://www.influxdata.com/time-series-platform/telegraf/" target="_blank">Telegraf</a> is _InfluxData_'s tool to
connect between southbound services (ex. system logs) and the storage layer. 

When Telegraf publishes metric data to an AnyLog node, AnyLog needs to know how to interpret the incoming JSON payload — 
which database and table to target, and how to extract the right fields from each message. This is handled by a 
**mapping policy**: a JSON structure stored in AnyLog's shared metadata layer that defines the full source-to-destination 
transformation.

Mapping policies let you:
- Rename or reformat incoming fields to match your table schema
- Apply type coercions (e.g. string → timestamp, string → decimal)
- Set fallback defaults when a field is missing
- Conditionally route data to different tables based on payload content


## What is a mapping policy 

Publishing data into AnyLog via (REST) POST or MQTT allows the user to correlate the JSON content with the database
table and column names to be used - ie mapping. 

AnyLog maps incoming JSON data to relational tables using mapping policies — JSON structures stored in the shared 
metadata layer. Each policy defines the source-to-destination transformation, specifying the target database, table, 
and schema.

Source data arrives in one of two shapes: flat key-value pairs (e.g., London Air Quality data), or a list of 
dictionaries where each entry is a reading. The core extraction mechanism is the _bring_ command, which pulls values 
from the source JSON and optionally transforms them. Mapping policies can be linked to data either directly via the run 
mqtt client command or by referencing a stored policy by ID.

This can be done in a hardcoded fashion or relative referencing. 

### Hardcoded Mapping 

A mapping policy has the following top-level keys:

| Key | Required | Purpose | 
|:---:| :---: | :---: | 
| id  | Yes | Unique policy identifier | 
| dbms | Yes | Target logical database | 
| table | Yes | Target table name | 
| readings | Yes - but could be empty | Key pointing to a list of readings in the source JSON | 
| condition | No | if statement to conditionally apply the policy  | 
| schema | Yes | Column definitions and mapping instructions | 
    

Each column in the schema is a dictionary with a bring expression (to extract the value), a type (string, integer, 
float, timestamp, bool, varchar, char), an optional condition, and an optional default fallback.

For blob data (images, video), additional keys like blob, extension, apply (e.g. base64 decoding), and hash extend the 
schema to route large objects to a dedicated object store while keeping a reference ID in the relational table.


#### Example

Lets take the example from [southbound overview](southound-overview.md#knowing-your-topics-and-schemas)

```anylog
<run msg client where
  broker = mqtt.mycompany.com and port = 1883 and
  topic = (
    name = sensors and
    dbms = my_data and
    table = temperature_readings and
    column.timestamp.timestamp = "bring [timestamp]" and
    column.device_name.str = "bring [device]" and
    column.value.float = "bring [temperature]"
  )>
```

A correlating alternative would be to use a mapping policy
```anylog
{
    "mapping": {
        "id": "sensors",
        "dbms": "my_data",
        "table": "temperature_readings",
        "readings": "", 
        "schema": {
            "timestamp": {
                "type": "timestamp", 
                "default": "now()",
                "bring": "[timestamp]"
            },
            "device_name": {
                "type": "string", 
                "default": "",
                "bring": ["device]"
            },
            "value": {
                "type": "float", 
                "default": null,
                "bring": "[value]"
            }
        }
    }
}
```

```
<run msg client where
  broker = mqtt.mycompany.com and port = 1883 and
  topic = (
    name = sensors and 
    policy = sensors
  )>    
```

## Publishing to AnyLog via Telegarf 

[missing intro - explaining how we do not know the data type or actual data thus are able to use "*" as an alternative]

### Steps 

The following provides step by step instructions on how to deploy Telegraf (via Docker) that publishes data into AnyLog  
via MQTT. The same can be replicated via REST as well. 

**Define an AnyLog Setup**

1. Define an AnyLog (operator) node to accept the data that has a local message broker 

2. Attach to the AnyLog node 

3. define the mapping policy
```anylog
policy_id = telegraf-mapping

<new_policy = {"mapping" : {
        "id" : !policy_id,
        "dbms" : !default_dbms,
        "table" : "bring [metrics][0][name] _ [metrics][0][tags][name]:[metrics][0][tags][host]",
        "readings" : "metrics",
        "schema" : {
                "timestamp" : {
                    "type" : "timestamp",
                    "default": "now()",
                    "bring" : "[timestamp]",
                    "apply" :  "epoch_to_datetime"
                },
                "*" : {
                    "type": "*",
                    "bring": ["fields", "tags"]
                }
         }
   }
}>

blockchain insert where policy=!new_policy and local=true and master=!ledger_conn
```

4. Initiate the message client to accept data from Telegraf via local
```shell
topic_name = telegraf 

<run msg client where broker=local and port=!anylog_broker_port and log=false and topic=(
    name=!topic_name and
    policy=!policy_id
)>


```

Steps 3 and 4 can be executed as one by running <code>process <a herf="https://github.com/AnyLog-co/deployment-scripts/blob/os-dev/sample-scripts/telegraf.al" target="_blank">!local_scripts/demo-scripts/telegraf.al</a></code>

**Start Telegraf with MQTT**

1. Define Telegraf's configuration file - named `telegraf.conf`

| Service Type |            Service           |
| :---: |:----------------------------:| 
| Input |              CPU             | 
| Input |             swap             | 
| Input |              mem             | 
| Input |              net             | 
| Output |             MQTT             |
| Output | REST - commented out example |

```editorconfig
[agent]
  interval = "5s"
  flush_interval = "5s"

# -----------------------
# INPUTS (what Telegraf collects)
# -----------------------

[[inputs.cpu]]
  percpu = true
  totalcpu = true

[[inputs.mem]]

[[inputs.swap]]

[[inputs.net]]

# -----------------------
# OUTPUT (MQTT)
# -----------------------

[[outputs.mqtt]]
  servers = ["tcp://192.168.65.3:32150"]  # use your broker
  topic = "telegraf"
  qos = 1

  data_format = "json"

  ## IMPORTANT: this gives you the structure similar to what you showed
  json_timestamp_units = "1s"

[[outputs.http]]
#   url = "http://192.168.65.3:32149"   # your REST endpoint
#   method = "POST"
# 
#   ## Headers (this matches your rest_post function)
#   headers = {
#     "command" = "data",
#     "topic" = "telegraf",
#     "User-Agent" = "AnyLog/1.23",
#     "Content-Type" = "application/json"
#   }
# 
#   ## Data format
#   data_format = "json"
# 
#   ## Timestamp format (seconds like your earlier examples)
#   json_timestamp_units = "1s"
```

2. Telegraf

```shell
docker run --rm \
  -v $(pwd)/telegraf.conf:/etc/telegraf/telegraf.conf \
  telegraf
```


**Validation**

From within AnyLog users can validate using some standard commands

* `get msg client` - view messages are accepted 
* `get streaming` - view how data is broken up into tables 
* `get operator` - view data once it has been processed 

