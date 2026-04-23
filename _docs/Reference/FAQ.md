---
title: FAQ & Troubleshooting
description: Common questions, known issues, and troubleshooting guidance for AnyLog deployments.
layout: page
---
<!--
## Changelog
- 2026-04-17 | Created document
--> 

---

## General

**Q: What is the difference between an Operator and a Publisher?**  
An Operator stores data locally in its own databases and responds to queries. A Publisher receives data files and routes them to Operator nodes — it does not store data itself. They cannot run on the same node.

**Q: What is the difference between a master node and a blockchain platform?**  
A master node is a simple AnyLog node that stores the metadata ledger in a local database and serves it to peers. A blockchain platform (e.g. Optimism) stores the ledger on a distributed, trustless chain. Either can be used; a blockchain is not required.

**Q: Can I run multiple AnyLog nodes on the same machine?**  
Yes. Each node needs its own set of ports (TCP, REST, broker) and its own root directory. Use different `ANYLOG_SERVER_PORT`, `ANYLOG_REST_PORT`, and `ANYLOG_BROKER_PORT` values per node.

**Q: How do I exit an AnyLog node?**  
```anylog
exit node
```

**Q: How do I run AnyLog in the background?**  
Use Docker with `-d` (detached mode), or configure AnyLog as a systemd service. When running in the background, the local CLI is disabled — use the Remote CLI or REST API instead.

---

## Networking

**Q: My node shows `Not connected` or peers can't reach it — what do I check?**

1. Confirm the TCP service is running: `get processes`
2. Confirm the correct IPs are published: `get connections`
3. Test local connectivity: `test node`
4. Test network connectivity: `test network`
5. Check firewall rules — the TCP and REST ports must be open inbound
6. If behind NAT, verify port forwarding is configured correctly
7. Check the blockchain sync is running and the local metadata file is populated: `get synchronizer`

**Q: What does `bind = true` vs `bind = false` mean?**  
`bind = true` — the service only accepts connections on the single specified IP.  
`bind = false` — the service accepts connections on all available IPs on that port. Use `false` when you want both local and external traffic accepted.

**Q: How do I check what ports AnyLog is listening on?**  
```anylog
get connections
```

**Q: The `test network` command shows some nodes as unreachable — is that a problem?**  
Not necessarily. Nodes may be offline, in a different network segment, or behind a firewall. Use `subset = true` in `run client` commands to tolerate partial responses:
```anylog
run client (blockchain get operator bring.ip_port, subset = true) get status
```

---

## Data ingestion

**Q: Data is arriving at the broker/MQTT but not appearing in the database — what do I check?**

1. Is the Streamer running? `get processes` — check `Streamer` row
2. Is the Operator running? Check `Operator` row in `get processes`
3. Is the watch directory being populated? `get !watch_dir`
4. Check the error directory for failed files: `get !err_dir`
5. Check the operator log: `get operator`
6. Confirm the database is connected: `get databases`
7. Confirm `create_table = true` is set in `run operator`, or create the table manually

**Q: What is the watch directory?**  
The watch directory is where JSON data files are staged before the Operator processes them. Any file placed in this directory is automatically picked up and ingested.
```anylog
get !watch_dir
```

**Q: Why are rows not appearing immediately after data arrives?**  
If the Streamer is running in buffered mode, data is held in memory until the time or volume threshold is reached. Default: 60 seconds or 10,000 bytes.
```anylog
get streaming                                              # check thresholds
set buffer threshold where write_immediate = true         # disable buffering
```

**Q: The Operator is running but showing errors — where do I look?**  
```anylog
get operator
get error log
```
Check the error directory: `get !err_dir`. Files moved there failed to process — inspect them for format issues.

**Q: How do I verify data is being ingested?**  
```anylog
get rows count where dbms = my_data
get operator inserts
get operator summary
```

---

## Queries

**Q: My query returns no results even though data exists — what do I check?**

1. Confirm the Operator node is running and the data is there: `get rows count`
2. Confirm the blockchain sync is up to date: `get synchronizer`
3. Use `run client (blockchain get operator bring.ip_port) get status` to confirm Operators are reachable
4. Check that the `dbms` and `table` names in the query match exactly what is in the database
5. Verify the time filter — `NOW() - N hours` not PostgreSQL `INTERVAL` syntax

**Q: Can I query data from a specific node only?**  
```anylog
run client (10.0.0.78:32048) sql my_data "select * from ping_sensor limit 10"
```

**Q: How do I profile slow queries?**  
```anylog
set query log on
set query log profile 5 seconds     # log queries slower than 5 seconds
get query log
```

---

## Docker & deployment

**Q: How do I view AnyLog logs in Docker?**  
```bash
docker logs [container-name]
docker attach --detach-keys=ctrl-d [container-name]   # attach to CLI
```

**Q: The container started but AnyLog isn't responding — what do I check?**

1. Check the container is running: `docker ps`
2. Attach to the CLI and check `get processes`
3. Verify the port mappings in your `docker run` or `docker-compose.yaml`
4. Check environment variables are set correctly (TCP port, REST port, etc.)

**Q: How do I update AnyLog?**  
```bash
docker pull anylogco/anylog-network:latest
docker stop [container-name]
docker rm [container-name]
docker run ... anylogco/anylog-network:latest
```

---

## AWS / cloud networking

**Q: I deployed on AWS (or GCP/Azure) and nodes can't connect to each other.**

- Ensure the security group (or firewall rule) allows **inbound TCP** on the AnyLog TCP and REST ports from the relevant IP ranges
- On AWS, the instance's public IP is typically the `external_ip`; the private IP is the `internal_ip`
- Use `bind = false` so the node accepts connections on all interfaces
- If using VPC peering or a private subnet, ensure routing tables allow traffic between instances

**Q: What MTU size should I use?**  
In some cloud and overlay network setups, the default MTU of 1500 bytes can cause packet fragmentation. If you see dropped connections or slow transfers, try reducing the MTU:
```bash
ip link set eth0 mtu 1400
```
Check your cloud provider's recommended MTU for your network type (e.g. AWS uses 9001 for jumbo frames in VPC, or 1500 for standard).

---

## Blockchain / metadata

**Q: `blockchain test` fails — what does that mean?**  
The local blockchain file is missing, corrupt, or empty. Re-sync from a peer:
```anylog
blockchain pull to json [peer-ip:port]
```

**Q: I added a policy but it's not visible on other nodes.**  
The blockchain sync interval controls when peers pick up new policies. Force an immediate sync:
```anylog
run blockchain sync
```
On peers:
```anylog
run blockchain sync
get metadata version     # confirm the version updated
```

**Q: How do I find the ID of a policy I just created?**  
```anylog
blockchain get [policy-type] where name = [name] bring [id]
```