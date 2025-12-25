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

from typing import Any

from gemseo.core.discipline import Discipline
from sqlalchemy import JSON
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlmodel import Field
from sqlmodel import SQLModel
from strenum import StrEnum

JobStatus = StrEnum("JobStatus", "created pending running failed finished")


class File(SQLModel, table=True):
    """The file SQLModel schema."""

    id: int | None = Field(
        default=None,
        primary_key=True,
        description="The file id",
    )
    filename: str = Field(description="The filename")
    unique_filename: str = Field(description="The unique filename (uuid)")
    sha256sum: str = Field(description="The sha256sum of the file")
    user_id: int = Field(foreign_key="user.id", description="The user id")


JobType = StrEnum("JobType", "execute execute_and_linearize")


class JobBase(SQLModel, table=False):
    """The id of the Job."""

    id: int | None = Field(
        default=None,
        primary_key=True,
        description="The id of the job",
    )
    name: str = Field(
        default="",
        description="The name of the Job",
    )
    discipline_class_name: str = Field(
        default="",
        description="The discipline class name",
    )
    discipline_options: dict[str, Any] = Field(
        sa_column=Column(JSON),
        default={},
        description="The discipline instance options",
    )
    job_type: JobType = Field(
        sa_column=Column(Enum(JobType)),
        default=JobType.execute.value,
        description="The type of the job",
    )
    job_status: JobStatus = Field(
        sa_column=Column(Enum(JobStatus)),
        description="The status of the job",
    )
    user_id: int = Field(
        foreign_key="user.id",
        description="The user id",
    )
    workdir: str = Field(
        default="",
        description="The working directory",
    )
    traceback: str = Field(
        default="",
        description="The traceback of the job, if an exception has been raised",
    )
    linearization_mode: Discipline.LinearizationMode = Field(
        sa_column=Column(Enum(Discipline.LinearizationMode)),
        default=Discipline.LinearizationMode.AUTO,
        description="The linearization mode",
    )
    linearize_options: dict[str, Any] = Field(
        sa_column=Column(JSON),
        default={},
        description="The linearization options",
    )
    differentiated_inputs: list[str] = Field(
        sa_column=Column(JSON),
        default=[],
        description="The inputs to differentiate",
    )
    differentiated_outputs: list[str] = Field(
        sa_column=Column(JSON),
        default=[],
        description="The outputs to differentiate",
    )


class Job(JobBase, table=True):
    """Store a Job in the database."""

    input_data: dict[str, Any] = Field(
        sa_column=Column(JSON),
        default={},
        description="The input data",
    )
    output_data: dict[str, Any] = Field(
        sa_column=Column(JSON),
        default={},
        description="The output data",
    )
    jacobian_data: dict[str, Any] = Field(
        sa_column=Column(JSON),
        default={},
        description="The Jacobian",
    )
