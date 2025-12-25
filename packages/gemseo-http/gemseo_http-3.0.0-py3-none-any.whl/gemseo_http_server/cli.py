# Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""CLI for the database management."""

from __future__ import annotations

from typing import TYPE_CHECKING

import typer
from pwdlib import PasswordHash
from sqlmodel import Session

from gemseo_http_server.database import User
from gemseo_http_server.database import create_db_and_tables
from gemseo_http_server.database import create_engine

if TYPE_CHECKING:
    from sqlalchemy import Engine

app = typer.Typer()


def main() -> None:
    """Typer entry point."""
    app()


@app.command()
def create_db() -> None:
    """Create the database."""
    try:
        engine = create_engine()
        create_db_and_tables(engine)
        typer.echo("Database and tables successfully created.")
    except Exception as e:  # noqa: BLE001
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)  # noqa: B904


@app.command()
def create_user_in_db(user_name: str, password: str) -> None:
    """Create a user in the database.

    Args:
         user_name: The username.
         password: The user password.
    """
    try:
        engine = create_engine()
        create_user(user_name, password, engine)
        typer.echo(f"User {user_name} successfully created.")
    except Exception as e:  # noqa: BLE001
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)  # noqa: B904


def create_user(user_name: str, password: str, engine: Engine) -> None:
    """Create a user in the database.

    Args:
         user_name: The user's name.
         password: The user's password.
         engine: The database engine.
    """
    password_hash = PasswordHash.recommended()
    hashed_password = password_hash.hash(password)
    with Session(engine) as session:
        user = User(username=user_name, hashed_password=hashed_password)
        session.add(user)
        session.commit()
