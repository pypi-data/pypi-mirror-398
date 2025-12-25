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

"""Database models."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlmodel
from sqlmodel import Column
from sqlmodel import Enum
from sqlmodel import Field
from sqlmodel import SQLModel
from strenum import StrEnum

from _gemseo_http_common import database  # noqa: F401
from gemseo_http_server.settings import settings

if TYPE_CHECKING:
    from sqlalchemy import Engine


class BaseUser(SQLModel, table=False, extra="forbid"):
    """Model for a user."""

    id: int | None = Field(
        default=None,
        primary_key=True,
        description="The user id",
    )
    username: str = Field(
        description="The username",
    )
    email: str = Field(
        "",
        description="The user email",
    )
    full_name: str = Field(
        "",
        description="The user full name",
    )
    disabled: bool = Field(
        False,
        description="Whether the user is disabled",
    )


class User(BaseUser, table=True):
    """The User in the database Pydantic model."""

    hashed_password: str = Field(description="The hashed password")


FileType = StrEnum("FileType", "input output")


class JobFile(SQLModel, table=True):
    """An indirection table linking files to jobs."""

    id: int | None = Field(
        default=None,
        primary_key=True,
        description="The id of the entry",
    )
    job_id: int = Field(
        foreign_key="job.id",
        description="The job id in Jobs database",
    )
    file_id: int = Field(
        foreign_key="file.id",
        description="The job id in Jobs database",
    )
    file_type: FileType = Field(
        sa_column=Column(Enum(FileType)),
        description="The filetype",
    )


def create_engine() -> Engine:
    """Create an SQLModel engine.

    Returns:
         The SQLModel engine.
    """
    sqlite_url = f"sqlite:///{settings.user_database_path}"
    connect_args = {"check_same_thread": False}
    return sqlmodel.create_engine(
        sqlite_url, echo=settings.database_debug, connect_args=connect_args
    )


def create_db_and_tables(engine: Engine) -> None:
    """Create the database and tables from the SQLModels.

    Args:
        engine: The database engine.
    """
    SQLModel.metadata.create_all(engine)
