<!--
Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->
# Web Application Deployment

The `gemseo-http` server is a FastAPI-based application that can be deployed for development or production.

## Development Environment

To set up a development environment, you can use `tox` to create an isolated Python environment:

```bash
tox -e py310 --develop
```
*(Replace `py310` with your desired Python version, e.g., `py39` or `py311`.)*

### Running the Web Application Locally

Once your environment is activated, you can run the web application using `uvicorn`:

```bash
uvicorn gemseo_http_server.app:app --reload
```

The application will be accessible at [http://localhost:8000](http://localhost:8000).

To use a specific configuration file, use the `--env-file` option:

```bash
uvicorn gemseo_http_server.app:app --reload --env-file /path/to/your/config.env
```

## Production Deployment

For production environments, it is essential to follow security best practices. Please refer to the [Security Notes](security_notes.md) section.

### Deployment Recommendations

Since `gemseo-http` is a standard FastAPI application, we recommend following the [FastAPI deployment documentation](https://fastapi.tiangolo.com/deployment/). Common approaches include using **Docker** or **Systemd**.

### Recommended Directory Structure

We suggest the following directory structure for a production installation:

| Directory | Description |
|-----------|-------------|
| `/opt/gemseo_http/bin` | Executable scripts and binaries |
| `/opt/gemseo_http/log` | Application log files |
| `/opt/gemseo_http/database` | SQLite database files (if used) |
| `/opt/gemseo_http/files` | Uploaded user files |
| `/opt/gemseo_http/workdir` | Temporary working directory for job execution |

### Example Deployment Script

Below is an example of a shell script (`run.sh`) to start the application with necessary environment variables:

```bash
#!/bin/bash
set -e

# Activate your Python environment
export PATH=/opt/miniconda3/envs/gemseo_http/bin/:$PATH

# Security: Generate a secret key (e.g., openssl rand -hex 32)
export GEMSEO_HTTP_SECRET_KEY="your-secret-key-here"

# Application paths
export GEMSEO_HTTP_ROOT_PATH=/opt/gemseo_http
export GEMSEO_HTTP_USER_DATABASE_PATH=$GEMSEO_HTTP_ROOT_PATH/database/database.db
export GEMSEO_HTTP_USER_FILE_DIRECTORY=$GEMSEO_HTTP_ROOT_PATH/files/
export GEMSEO_HTTP_USER_WORKSPACE_EXECUTION=$GEMSEO_HTTP_ROOT_PATH/workdir/

# Run the server
uvicorn gemseo_http_server.app:app --host 0.0.0.0 --port 8000
```

### Systemd Service Configuration

To manage the application as a system service on Linux, you can create a Systemd unit file (e.g., `/etc/systemd/system/gemseo-http.service`):

```ini
[Unit]
Description=GEMSEO HTTP Service
After=network.target

[Service]
Type=simple
User=gemseo_http
Group=gemseo_http
Restart=always
RestartSec=5
ExecStart=/bin/bash /opt/gemseo_http/bin/run.sh

StandardOutput=append:/opt/gemseo_http/log/access.log
StandardError=append:/opt/gemseo_http/log/error.log

[Install]
WantedBy=multi-user.target
```

Alternatively, you can use `docker-compose` for containerized deployments.
