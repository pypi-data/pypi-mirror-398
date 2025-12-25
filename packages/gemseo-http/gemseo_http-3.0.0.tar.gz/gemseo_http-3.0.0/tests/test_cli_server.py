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

from __future__ import annotations

import pytest
import sqlmodel
from sqlmodel import Session
from sqlmodel import StaticPool
from sqlmodel import select
from typer.testing import CliRunner

from gemseo_http_server.cli import app as cli_app
from gemseo_http_server.database import User
from gemseo_http_server.database import create_db_and_tables

runner = CliRunner()


@pytest.fixture
def mock_engine_raise_error(mocker):
    def fake_create_engine():
        msg = "Cannot create the database engine."
        raise RuntimeError(msg)

    mocker.patch("gemseo_http_server.cli.create_engine", new=fake_create_engine)


@pytest.fixture
def mock_engine(mocker):
    """Fixture to mock the database engine."""
    engine = sqlmodel.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True,
    )
    mocker.patch("gemseo_http_server.cli.create_engine", return_value=engine)
    return engine


def test_create_db_and_tables(mock_engine):
    """Ensure the database and tables are created successfully."""
    result = runner.invoke(cli_app, ["create-db"])
    assert result.exit_code == 0
    assert "Database and tables successfully created." in result.stdout


def test_create_db_and_tables_failure(mock_engine_raise_error):
    """Ensure the database and tables are not created successfully."""
    result = runner.invoke(cli_app, ["create-db"])
    assert result.exit_code == 1
    assert "Error: Cannot create the database engine." in result.stdout


def test_create_user_in_db_success(mock_engine):
    """Ensure the user is created successfully in the database."""
    user_name = "test_user"
    password = "test_password"

    create_db_and_tables(mock_engine)

    result = runner.invoke(cli_app, ["create-user-in-db", user_name, password])
    assert result.exit_code == 0
    assert "User test_user successfully created." in result.stdout

    with Session(mock_engine) as session:
        statement = select(User).where(User.username == user_name)
        user = session.exec(statement).first()

        assert user is not None
        assert user.username == user_name
        # Ensure the password is stored as a hash
        assert user.hashed_password != password


def test_create_user_in_db_failure(mock_engine_raise_error):
    """Ensure the user is not created successfully in the database."""
    user_name = "test_user"
    password = "test_password"
    result = runner.invoke(cli_app, ["create-user-in-db", user_name, password])
    assert result.exit_code == 1
    assert "Error: Cannot create the database engine." in result.stdout
