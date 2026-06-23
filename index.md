---
layout: default
title: AnyLog Documentation
---
<!--
## Changelog
- 2026-04-20 | Created document
- 2026-04-24 | updated document with new image + proper links
-->

<div class="home-hero">
  <h1>AnyLog Documentation</h1>
  <p>AnyLog — Enable independent (industrial) databases to function as a single logical data network.</p>
</div>

[//]: # (<div class="home-diagram" align="center">)

[//]: # (    <object type="image/svg+xml" data="{{ '/assets/img/anylog_network_fabric_animated.svg' | relative_url }}" width="10%" height="10%">)

[//]: # (    </object>)

[//]: # (</div>)

<div class="home-diagram" align="center">
  {% include anylog_network_fabric_animated.svg %}
</div>

<div class="home-cards" align="center">
  <a class="home-card" href="{{ '/docs/getting-started/' | relative_url }}">
    <div class="home-card-icon">🚀</div>
    <h3>Getting Started</h3>
    <p>Install, configure, and run your first AnyLog node.</p>
  </a>
  <a class="home-card" href="{{ '/docs/adding-data/' | relative_url }}">
    <div class="home-card-icon">📥</div>
    <h3>Southbound services</h3>
    <p>OPC-UA, Modbus TCP, REST, Kafka, gRPC — all the ways to get data in.</p>
  </a>
  <a class="home-card" href="{{ '/docs/queries/' | relative_url }}">
    <div class="home-card-icon">🔍</div>
    <h3>Northbound services</h3>
    <p>Query distributed edge nodes via REST, Kafka, and BI tools.</p>
  </a>
  <a class="home-card" href="{{ '/docs/readme/' | relative_url }}">
    <div class="home-card-icon">❓</div>
    <h3>Docs index</h3>
    <p>Browse the source documentation index and topic map.</p>
  </a>
</div>
