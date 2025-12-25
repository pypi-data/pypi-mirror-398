<!--
Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

# Setting up the SQL Database

The web application and background worker rely on a SQL database to store essential data, including:

- **User information**: Credentials and permissions.
- **Job details**: Execution parameters, status, and history.
- **File records**: Metadata for uploaded and generated files.

## Using Alembic (Recommended)

[Alembic](https://alembic.sqlalchemy.org/en/latest/) is the preferred tool for managing database schemas and migrations in `gemseo-http`. It ensures your database structure is consistent and can be easily upgraded.

To bootstrap a new database or migrate an existing one, follow these steps:

1. **Configure Alembic**: Edit the `alembic.ini` file in the project root. Specifically, ensure the `sqlalchemy.url` parameter points to your database. For SQLite, this would look like:
   ```ini
   sqlalchemy.url = sqlite:///./database.db
   ```
2. **Run Migrations**: Execute the following command to bring the database to the latest version:
   ```bash
   alembic upgrade head
   ```

If the database file does not exist, Alembic will create it automatically.

## Using the `gemseo-http` CLI

For simple setups, you can use the built-in CLI to initialize the database. Note that this method does not support easy schema migrations in the future.

1. **Navigate** to your desired database directory (e.g., `/opt/gemseo_http/database/`).
2. **Execute** the initialization command:
   ```bash
   gemseo-http create-db
   ```

## Managing Users

User management is currently handled through the command-line interface.

### Adding a User

To create a new user in the database, use the following command:

```bash
gemseo-http create-user-in-db <username> <password>
```

Replace `<username>` and `<password>` with the desired credentials. These will be used by the `HTTPDiscipline` client for authentication.
