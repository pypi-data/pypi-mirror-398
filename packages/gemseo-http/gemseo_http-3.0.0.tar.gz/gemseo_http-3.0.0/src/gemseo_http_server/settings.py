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

"""Settings."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings, env_prefix="GEMSEO_HTTP_"):
    """The application settings."""

    secret_key: str = Field(
        "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="The secret key to encode/decode the JSON web tokens.",
    )
    algorithm: str = Field(
        "HS256", description="The algorithm to encode/decode the JSON web tokens."
    )
    access_token_expire_minutes: int = Field(
        10080, description="The expiration time for the token."
    )
    user_database_path: Path = Field(
        "./database.db",
        description="The path to the user database.",
    )
    user_file_directory: Path = Field(
        "./files/", description="The file workspace directory."
    )
    user_workspace_execution: Path = Field(
        "./workdir/", description="The user workspace execution."
    )
    huey_database_path: Path = Field(
        "./huey.db", description="The path to the Huey task manager database."
    )
    huey_immediate_mode: bool = Field(
        False, description="Whether to trigger the Huey immediate mode."
    )
    huey_immediate_mode_in_memory: bool = Field(
        False, description="Whether to trigger the Huey immediate mode in-memory."
    )
    fastapi_debug: bool = Field(
        False, description="Whether to run FastAPI in debug mode."
    )
    openapi_version: str = Field(
        "3.0.0", description="The OpenAPI specification version to use."
    )
    database_debug: bool = Field(
        False, description="Whether to run SQLModel in debug mode."
    )
    enable_discipline_counters: bool = Field(
        True, description="Whether to enable the discipline counters."
    )
    enable_discipline_cache: bool = Field(
        True, description="Whether to enable the discipline cache."
    )
    enable_progress_bar: bool = Field(
        False, description="Whether to enable the progress_bar."
    )
    enable_function_counters: bool = Field(
        True, description="Whether to enable the function counters."
    )


settings = Settings()
