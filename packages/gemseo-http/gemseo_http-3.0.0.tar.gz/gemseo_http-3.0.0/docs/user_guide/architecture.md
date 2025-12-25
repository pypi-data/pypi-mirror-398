<!--
Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

# Architecture

## A client-server architecture

The `gemseo-http` plugin implements a client-server architecture based on the HTTP protocol.
The server is a [FastAPI](https://fastapi.tiangolo.com/) application that exposes GEMSEO disciplines as a RESTful service.
At server startup, available disciplines are automatically detected via the GEMSEO factory mechanism.
For each detected discipline, the server exposes its input and output grammars, allowing clients to discover the required data structures.

The server supports two execution modes for remote disciplines:

- **Synchronous mode**: The client waits for the server to process the request and return the results in the same HTTP connection. This is suitable for fast-running disciplines.
- **Asynchronous mode**: The client submits a job and receives a task identifier. It can then poll the server or wait for a notification to retrieve the results once the execution is complete. This is recommended for long-running disciplines.

### Asynchronous Execution Stack

In asynchronous mode, the architecture incorporates a message broker and a task manager to decouple job submission from execution:

- **Message Broker**: Used to queue execution requests. While `gemseo-http` currently uses an [SQLite](https://sqlite.org/) database as the default broker, it can be configured to use more robust systems like RabbitMQ or Redis.
- **Task Manager**: [Huey](https://huey.readthedocs.io/) is used as the task consumer. It was chosen for its cross-platform compatibility, particularly its ability to run natively on Windows.

### Data Persistence and State

Although the web service itself is stateless, `gemseo-http` must manage the state of discipline executions and file transfers across multiple HTTP calls. This is handled as follows:

- **Execution Metadata**: Information about each execution (parameters, inputs, outputs, status) is stored in a SQL database. SQLite is used by default, but production environments can use databases like PostgreSQL.
- **Session Management**: Clients maintain a session identifier to track their executions and retrieve results asynchronously.
- **File Handling**: The server manages a workspace for each execution to store uploaded input files and generated output files, ensuring they are available for download by the client.

![gemseo-http architecture](img/gemseo_http_architecture.png)
