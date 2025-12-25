<!--
Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->
# Configuration

The `gemseo-http` server is configured primarily through environment variables. These can be set directly in your shell or provided via a `.env` file in the project root.

## Environment Variables

### Authentication Settings

- **`GEMSEO_HTTP_SECRET_KEY`**
  The secret key used for signing and verifying JSON Web Tokens (JWT). For production, use a strong, randomly generated string (e.g., `openssl rand -hex 32`).

- **`GEMSEO_HTTP_ALGORITHM`**
  The cryptographic algorithm used for JWT operations. Defaults to `HS256`.

- **`GEMSEO_HTTP_ACCESS_TOKEN_EXPIRE_MINUTES`**
  The validity period (in minutes) for an access token before it expires.

### Storage and Workspace

- **`GEMSEO_HTTP_USER_DATABASE_PATH`**
  The file system path to the SQLite database where user data and job metadata are stored.

- **`GEMSEO_HTTP_USER_FILE_DIRECTORY`**
  The directory where uploaded user files (input files) are permanently stored.

- **`GEMSEO_HTTP_USER_WORKSPACE_EXECUTION`**
  The root directory used as a workspace for discipline executions. Each job will have its own subdirectory here.

### Task Queue (Huey)

- **`GEMSEO_HTTP_HUEY_DATABASE_PATH`**
  The file system path to the SQLite database used by Huey as a message broker.

- **`GEMSEO_HTTP_HUEY_IMMEDIATE_MODE`**
  If set to `True`, Huey will run tasks synchronously in the same process as the web application. This is useful for debugging but not recommended for production.

- **`GEMSEO_HTTP_HUEY_IMMEDIATE_MODE_IN_MEMORY`**
  If set to `True`, Huey uses an in-memory storage for tasks. This is primarily for unit testing.

### Debugging

- **`GEMSEO_HTTP_FASTAPI_DEBUG`**
  Enables FastAPI's debug mode, providing more detailed error messages in responses.

- **`GEMSEO_HTTP_DATABASE_DEBUG`**
  Enables SQLModel/SQLAlchemy debug logging to see all executed SQL queries.

## Using a `.env` file

A template `.env` file with default values is provided in the repository root. You can copy it and modify the values to suit your environment:

```bash
cp .env.sample .env
# Edit .env with your favorite editor
```
