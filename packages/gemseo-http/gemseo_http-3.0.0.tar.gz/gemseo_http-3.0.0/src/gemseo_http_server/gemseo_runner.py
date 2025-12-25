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

"""Runner of GEMSEO discipline."""

from __future__ import annotations

import json
import traceback
from os import chdir
from pathlib import Path
from typing import TYPE_CHECKING

from gemseo import create_discipline
from huey import SqliteHuey
from sqlmodel import Session
from sqlmodel import select

from _gemseo_http_common.data_conversion import convert_dict_array_to_list
from _gemseo_http_common.data_conversion import convert_dict_list_to_array
from _gemseo_http_common.data_conversion import convert_dict_of_dict_array_to_list
from _gemseo_http_common.database import Job
from _gemseo_http_common.database import JobStatus
from _gemseo_http_common.database import JobType
from gemseo_http_server.database import create_engine
from gemseo_http_server.settings import settings

if TYPE_CHECKING:
    from sqlalchemy import Engine

# TODO: A factory of Huey backends would be better.
huey = SqliteHuey(
    filename=settings.huey_database_path,
    immediate=settings.huey_immediate_mode,
    immediate_use_memory=settings.huey_immediate_mode_in_memory,
)


@huey.task()
def execute_discipline_async(job_id: int) -> None:
    """Execute the discipline in background.

    Args:
        job_id: The id of the job.
    """
    engine = create_engine()
    execute_discipline(job_id, engine)


def execute_discipline(job_id: int, engine: Engine) -> None:
    """Execute the discipline in background.

    Args:
        job_id: The id of the job.
        engine: The database engine.
    """
    with Session(engine) as session:
        statement = select(Job).where(Job.id == job_id)
        results = session.exec(statement)
        job = results.one()
        initial_directory = Path.cwd()

        try:
            job.job_status = JobStatus.running
            session.commit()
            session.refresh(job)

            # Chdir shall be converted with a context manager,
            # available in Python 3.11 in contextlib
            # https://docs.python.org/3/library/contextlib.html#contextlib.chdir
            chdir(job.workdir)

            disc = create_discipline(
                job.discipline_class_name, **job.discipline_options
            )

            if not job.input_data:
                # WHY do we need to record the inputs in this case?
                input_data = convert_dict_array_to_list(disc.io.input_grammar.defaults)
                input_data_numpy = None
            else:
                input_data = job.input_data
                input_data_numpy = convert_dict_list_to_array(input_data)

            output_data = disc.execute(input_data_numpy)

            # WHY is this needed?
            job.input_data = json.dumps(input_data)
            job.output_data = convert_dict_array_to_list(output_data)

            if job.job_type == JobType.execute_and_linearize:
                disc.add_differentiated_inputs(job.differentiated_inputs)
                disc.add_differentiated_outputs(job.differentiated_outputs)
                disc.linearization_mode = job.linearization_mode
                jac = disc.linearize(input_data_numpy, **job.linearize_options)
                job.jacobian_data = convert_dict_of_dict_array_to_list(jac)

            job.job_status = JobStatus.finished

            chdir(initial_directory)

            session.commit()
            session.refresh(job)

        except BaseException:  # noqa: BLE001
            job.job_status = JobStatus.failed
            job.traceback = traceback.format_exc()
            session.commit()
            chdir(initial_directory)
