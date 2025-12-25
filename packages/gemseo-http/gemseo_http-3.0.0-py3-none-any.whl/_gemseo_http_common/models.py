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
"""Pydantic models."""

from __future__ import annotations

from typing import Any

from gemseo.core.discipline import Discipline
from pydantic import BaseModel
from pydantic import Field

from _gemseo_http_common.database import File


class DisciplineOptions(BaseModel):
    """The discipline options, if any."""

    discipline_options: dict[str, Any] = Field(
        default={}, description="The options of the discipline."
    )


class ExecuteInput(DisciplineOptions):
    """The model for a discipline execution."""

    name: str = Field(default="", description="The name of the discipline.")

    input_data: dict[str, list[float | int | str] | str | int | float] | str = Field(
        default={}, description="The input data of the discipline."
    )

    input_data_type: str = Field(
        default="json", description="The discipline input data type."
    )

    input_files: list[File] = Field(default=[], description="The input files.")

    linearize: bool = Field(
        default=False, description="Whether to linearize the discipline."
    )

    linearization_mode: Discipline.LinearizationMode = Field(
        default=Discipline.LinearizationMode.AUTO,
        description="The linearization mode.",
    )

    linearize_options: dict[str, Any] = Field(
        default={}, description="The linearization options."
    )

    differentiated_inputs: list[str] = Field(
        default=[], description="The inputs to differentiate."
    )

    differentiated_outputs: list[str] = Field(
        default=[], description="The outputs to differentiate."
    )
