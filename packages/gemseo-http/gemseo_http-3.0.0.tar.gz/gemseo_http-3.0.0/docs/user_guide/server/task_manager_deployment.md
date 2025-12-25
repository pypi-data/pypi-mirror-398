<!--
Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->
# Task Manager Deployment

While the web application can execute synchronous jobs, using asynchronous execution is recommended for tasks that take more than a few seconds.

For asynchronous requests, the **Huey** task manager must be used to process jobs in the background. This decouples the web application from the computationally intensive discipline executions, ensuring the service remains responsive.

## Why use a Task Manager?

- **Non-blocking Execution**: Long-running disciplines run in the background without blocking the web server's worker threads.
- **Maintenance**: The web application can be restarted or updated while background jobs continue to run.
- **Scalability**: Multiple Huey workers can be deployed to handle a high volume of concurrent execution requests.

Currently, `gemseo-http` uses **SQLite** as the default message broker for Huey. While Huey supports other brokers like Redis or RabbitMQ, the current implementation is optimized for SQLite to simplify cross-platform deployment.

## Development Mode

In a development environment, you can run the Huey consumer interactively:

```bash
huey_consumer.exe gemseo_http_server.gemseo_runner.huey
```

### Advanced Options

You can configure the number of worker threads or processes. For example, to use two worker threads:

```bash
huey_consumer.exe gemseo_http_server.gemseo_runner.huey -k thread -w 2
```

For more options, please refer to the [Huey documentation](https://huey.readthedocs.io/en/latest/consumer.html).

## Production Deployment

Similar to the web application, it is recommended to run the Huey worker as a system service using **Systemd** or **Docker**.

### Example Worker Script

Create a script (e.g., `run_worker.sh`) to start the Huey consumer with the necessary environment variables:

```bash
#!/bin/bash
set -e

# Activate your Python environment
export PATH=/opt/miniconda3/envs/gemseo_http/bin/:$PATH

# Application paths (must match the web application configuration)
export GEMSEO_HTTP_ROOT_PATH=/opt/gemseo_http
export GEMSEO_HTTP_HUEY_DATABASE_PATH=$GEMSEO_HTTP_ROOT_PATH/database/huey.db
export GEMSEO_HTTP_USER_DATABASE_PATH=$GEMSEO_HTTP_ROOT_PATH/database/database.db
export GEMSEO_HTTP_USER_FILE_DIRECTORY=$GEMSEO_HTTP_ROOT_PATH/files/
export GEMSEO_HTTP_USER_WORKSPACE_EXECUTION=$GEMSEO_HTTP_ROOT_PATH/workdir/

# Run the Huey consumer
huey_consumer gemseo_http_server.gemseo_runner.huey
```

### Systemd Service Configuration

To manage the Huey worker as a system service, create a Systemd unit file (e.g., `/etc/systemd/system/gemseo-http-worker.service`):

```ini
[Unit]
Description=GEMSEO HTTP Task Worker
After=network.target

[Service]
Type=simple
User=gemseo_http
Group=gemseo_http
Restart=always
RestartSec=5
ExecStart=/bin/bash /opt/gemseo_http/bin/run_worker.sh

StandardOutput=append:/opt/gemseo_http/log/worker_access.log
StandardError=append:/opt/gemseo_http/log/worker_error.log

[Install]
WantedBy=multi-user.target
```
