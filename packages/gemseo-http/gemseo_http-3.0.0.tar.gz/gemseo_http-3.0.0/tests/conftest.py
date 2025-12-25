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

"""HTTP fixtures."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

import pytest
import sqlmodel
from gemseo.disciplines.factory import DisciplineFactory
from gemseo.utils.testing.pytest_conftest import *  # noqa: F403
from sqlalchemy import StaticPool
from starlette.testclient import TestClient

from _gemseo_http_common.database import Job
from gemseo_http_server.app import app
from gemseo_http_server.app import settings
from gemseo_http_server.cli import create_user
from gemseo_http_server.database import User
from gemseo_http_server.database import create_db_and_tables
from gemseo_http_server.database import create_engine
from gemseo_http_server.security import get_current_active_user

if TYPE_CHECKING:
    from sqlalchemy import Engine

FAKE_USER = User(username="test", id=0, email="test@test.com", full_name="Test Test")


async def fake_get_current_active_user() -> User:  # noqa: RUF029
    """Provide unconditionally the test user for test purposes."""
    return FAKE_USER


@pytest.fixture(autouse=True)
def sqldb_fixture():
    """Inject an in-memory DB fixture."""
    engine = sqlmodel.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True,
    )
    create_db_and_tables(engine)
    create_user("test", "test", engine)

    async def fake_create_engine() -> Engine:  # noqa: RUF029
        return engine

    app.dependency_overrides[create_engine] = fake_create_engine
    yield engine
    app.dependency_overrides[create_engine] = create_engine


@pytest.fixture
def fake_current_active_user():
    """Bypass the user authentification on server side for testing purposes."""
    app.dependency_overrides[get_current_active_user] = fake_get_current_active_user
    yield
    app.dependency_overrides[get_current_active_user] = get_current_active_user


@pytest.fixture(autouse=True)
def setup_environment_variables():
    os.environ["GEMSEO_PATH"] = str(Path(__file__).parent / "data")  # noqa: F405
    DisciplineFactory().update()


@pytest.fixture
def test_client():
    """Return a TestClient for testing."""
    return TestClient(app, backend_options={"loop_factory": asyncio.new_event_loop})


@pytest.fixture(autouse=True)
def setup_settings(tmp_path):
    """Configure the settings."""
    settings.user_workspace_execution = tmp_path / "workspace/"
    settings.user_file_directory = tmp_path / "files/"
    settings.huey_database_path = tmp_path / "huey.db"
    settings.huey_immediate_mode = True
    settings.huey_immediate_mode_in_memory = True
    chunks_path = settings.user_file_directory / "chunks"
    os.makedirs(chunks_path)  # noqa: F405


@pytest.fixture  # noqa: F405
def create_fake_poll_job():
    """Create a fake poll job method for testing purposes."""

    def fake_poll_job(job_id):
        """Fake poll job method for testing purposes.

        Args:
            job_id: The job id.

        Returns:
            A fake pending Job object.
        """
        time.sleep(2)
        return Job(id=job_id, user_id=1, job_status="pending")

    return fake_poll_job
