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

import httpx
import pytest
from typer.testing import CliRunner

from gemseo_http._cli import app as cli_app

runner = CliRunner()


@pytest.fixture
def mock_httpx_post_valid(mocker):
    """Mock httpx.post method."""
    response = httpx.Response(status_code=200, json={"access_token": "test_token"})
    return mocker.patch("httpx.Client.post", return_value=response)


@pytest.fixture
def mock_httpx_post_invalid(mocker):
    """Mock httpx.post method."""
    response = httpx.Response(
        status_code=401, content="Incorrect username or password."
    )
    return mocker.patch("httpx.Client.post", return_value=response)


def test_generate_token_valid_credentials(mock_httpx_post_valid):
    """Check that valid credentials return a token."""
    result = runner.invoke(
        cli_app,
        ["http://localhost:8000", "test", "test"],
    )
    assert result.exit_code == 0
    assert "test_token" in result.stdout


def test_generate_token_invalid_credentials(mock_httpx_post_invalid):
    """Check behavior for invalid credentials."""
    result = runner.invoke(
        cli_app,
        ["http://localhost:8000", "invalid_user", "invalid_password"],
    )
    assert result.exit_code != 0
    assert "Incorrect username or password." in result.stdout
