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

import httpx
import typer

app = typer.Typer()


def main() -> None:
    """Typer entry point."""
    app()


@app.command()
def generate_token(domain_port: str, user_name: str, password: str) -> None:
    """Generate a token based on a login and a password."""
    authenticate_endpoint = f"{domain_port}/token"
    http_client = httpx.Client()
    data = {"username": user_name, "password": password}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    request = http_client.post(
        authenticate_endpoint,
        data=data,
        headers=headers,
    )
    if request.status_code != 200:
        print("Incorrect username or password.")  # noqa: T201
        raise typer.Exit(code=1)
    post_data = request.json()
    token = post_data["access_token"]
    print(f"Token: {token}")  # noqa: T201
    raise typer.Exit(code=0)
