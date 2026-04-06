---
layout: default
title: AnyLog Documentation
---

<div class="home-hero">
  <h1>AnyLog Documentation</h1>
  <div>
    <p align="justified">AnyLog — Enable independent (industrial) databases to function as a single logical data network.</p>
  </div>
</div>

<div class="home-cards">
  <a class="home-card" href="{{ '/docs/introduction/' | relative_url }}">
    <div class="home-card-icon">🏗️</div>
    <h3>Architecture</h3>
    <p>Node types, network flow, blockchain layer, and how querying works.</p>
  </a>
  <a class="home-card" href="{{ '/docs/data-ingestion-overview/' | relative_url }}">
    <div class="home-card-icon">📥</div>
    <h3>Data Ingestion</h3>
    <p>REST, MQTT, Kafka, OPC-UA — all the ways to get data in.</p>
  </a>
  <a class="home-card" href="{{ '/docs/msg-client/' | relative_url }}">
    <div class="home-card-icon">🔀</div>
    <h3>Message Client</h3>
    <p>Map incoming messages to database tables using <code>run msg client</code>.</p>
  </a>
  <a class="home-card" href="{{ '/docs/querying-overview/' | relative_url }}">
    <div class="home-card-icon">🔍</div>
    <h3>Querying Data</h3>
    <p>Run SQL queries across distributed edge nodes from a query node.</p>
  </a>
</div>
