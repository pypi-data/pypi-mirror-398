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

"""Job creation."""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from fastapi import status
from fastapi.responses import FileResponse
from sqlmodel import Session
from sqlmodel import select
from strenum import StrEnum

from _gemseo_http_common.constants import ExecutionMode
from _gemseo_http_common.database import File
from _gemseo_http_common.database import Job
from _gemseo_http_common.database import JobStatus
from _gemseo_http_common.database import JobType
from gemseo_http_server.database import FileType
from gemseo_http_server.database import JobFile
from gemseo_http_server.gemseo_runner import execute_discipline
from gemseo_http_server.gemseo_runner import execute_discipline_async
from gemseo_http_server.settings import settings

if TYPE_CHECKING:
    from fastapi import BackgroundTasks
    from sqlalchemy import Engine
    from starlette.responses import Response

    from _gemseo_http_common.models import ExecuteInput
    from gemseo_http_server.database import User

DataType = StrEnum("DataType", "json")


def get_jobs_for_user(user_id: int, engine: Engine) -> list[Job]:
    """Return the jobs of a user.

    Args:
        user_id: The user id.
        engine: The database engine.

    Returns:
        The jobs belonging to the user.
    """
    with Session(engine) as session:
        statement = select(Job).where(Job.user_id == user_id)
        return session.exec(statement).all()


def get_job_from_id(
    job_id: int,
    data_type: DataType,
    long_polling: bool,
    timer: float,
    engine: Engine,
    timeout: float = 100.0,
) -> Job | None:
    """Return a Job in the database from its id.

    Args:
         job_id: The id of the job in database.
         data_type: The type of data provided.
         long_polling: Whether the call is for a long-polling or not.
         timer: The overall time passed in querying the data.
         engine: The database engine.
         timeout: The timeout for the long polling.

    Returns:
        A job instance.
    """
    if data_type != DataType.json:
        msg = "Unknown %s"
        raise ValueError(msg, data_type)

    with Session(engine) as session:
        results = session.get(Job, job_id)

    job_finished = results.job_status in (JobStatus.finished, JobStatus.failed)
    elapsed = time.time() - timer

    if long_polling and not job_finished and elapsed < timeout:
        # Add sleep time between two calls to the database.
        time.sleep(timeout / 100)
        # Recursive call to enable long-polling
        return get_job_from_id(job_id, data_type, long_polling, timer, engine, timeout)

    return results


def set_leaf(
    tree: dict,
    branches: list[str],
    leaf: any,
) -> None:
    """Set a terminal element to *leaf* within nested dictionaries.

    *branches* defines the path through dictionnaries.

    Example:
    >>> t = {}
    >>> set_leaf(t, ["b1", "b2", "b3"], "new_leaf")
    >>> print t
    {'b1': {'b2': {'b3': 'new_leaf'}}}
    """
    if len(branches) == 1:
        tree[branches[0]] = leaf
        return
    if branches[0] not in tree:
        tree[branches[0]] = {}
    set_leaf(tree[branches[0]], branches[1:], leaf)


def get_file_paths(
    user_id: int,
    job_id: str,
    response: Response,
    engine: Engine,
) -> dict[str, Any] | str:
    """Return a files in the database from its id.

    Args:
        user_id: The user id.
        job_id: The id of the job in database.
        response: The request response.
        engine: The database engine.

    Returns:
        The file paths.
    """
    with Session(engine) as session:
        result = session.get(Job, job_id)
        if result.user_id != user_id:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "You are not allowed to access the files of this job."

    start_path = str(Path(result.workdir))
    tree = {}
    for root, dirs, files in os.walk(start_path):
        branches = ["."]
        if root != start_path:
            relpath_split = Path(os.path.relpath(root, start_path)).parts
            branches.extend(relpath_split)
        set_leaf(
            tree, branches, dict([(d, {}) for d in dirs] + [(f, None) for f in files])
        )
    return tree["."]


def download_file_from_job_id(
    user_id: int,
    job_id: str,
    response: Response,
    filename: str,
    engine: Engine,
) -> FileResponse | str:
    """Return a Job in the database from its id.

    Args:
        user_id: The user id.
        job_id: The id of the job in a database.
        response: The job response.
        filename: The file name.
        engine: The database engine.

    Returns:
        A job instance.
    """
    with Session(engine) as session:
        result = session.get(Job, job_id)
        if result.user_id == user_id:
            filepath = Path(result.workdir) / filename
            if Path.is_file(filepath):
                return FileResponse(path=filepath, filename=filename)
            response.status_code = status.HTTP_404_NOT_FOUND
            return "The file has not been found."

        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "You are not allowed to access the files of this job."


def create_job_in_database(
    user: User,
    discipline_class_name: str,
    body: ExecuteInput | None,
    engine: Engine,
    execution_mode: ExecutionMode,
    background_task: BackgroundTasks,
    response: Response,
) -> Response | Job:
    """Create and manage a new job in the database.

    Args:
        user: The authenticated user who is creating the job.
        discipline_class_name: The name of the discipline class related to the job.
        body: The request payload containing job parameters like input data,
            linearization settings, and input files.
        engine: The engine used to interface with the database.
        execution_mode: The mode x indicating whether the job should run
            synchronously or asynchronously.
        background_task: The queue for asynchronous execution.
        response: The object used to set the API call's HTTP status.

    Returns:
        Either job created and its details, or
        response indicating the status of an asynchronous execution request.
    """
    with Session(engine) as session:
        body_name = "undefined" if not body else body.name
        job = Job(name=body_name, job_status=JobStatus.created, user_id=user.id)
        job.discipline_class_name = discipline_class_name

        if body:
            job.discipline_options = body.discipline_options
        else:
            job.discipline_options = {}

        session.add(job)
        session.commit()
        session.refresh(job)

        workdir = Path(settings.user_workspace_execution) / user.username / str(job.id)
        Path.mkdir(workdir, parents=True)
        job.workdir = str(workdir)

        input_data = body.input_data if body and body.input_data else None

        job.input_data = input_data
        job.discipline_class_name = discipline_class_name

        # Linearization options
        if body and body.linearize:
            job.job_type = JobType.execute_and_linearize
            job.differentiated_inputs = body.differentiated_inputs
            job.differentiated_outputs = body.differentiated_outputs
            job.linearize_options = body.linearize_options
            job.linearization_mode = body.linearization_mode
        else:
            job.job_type = JobType.execute

        session.add(job)
        session.commit()
        session.refresh(job)

        input_files = ([] if not body.input_files else body.input_files) if body else []

        # Copy input files to work directory
        for unique_filename in input_files:
            statement_file = select(File).where(
                File.unique_filename == unique_filename.unique_filename
            )
            results = session.exec(statement_file)
            job_file = results.one()
            job_file_db = JobFile(
                job_id=job.id, file_id=job_file.id, file_type=FileType.input
            )
            job_file_db.job_id = job.id
            job_file_db.file_id = job_file.id
            job_file_db.file_type = FileType.input
            session.add(job_file_db)
            src_path = Path(settings.user_file_directory) / Path(
                job_file.unique_filename
            )
            dest_path = Path(job.workdir) / Path(job_file.filename)
            shutil.copy(src_path, dest_path)

        session.commit()
        session.refresh(job)

        if execution_mode == ExecutionMode.asynchronous:
            background_task.add_task(execute_discipline_async, job.id)
            response.status_code = status.HTTP_202_ACCEPTED
            job.job_status = JobStatus.pending
            session.commit()
            session.refresh(job)
        elif execution_mode == ExecutionMode.synchronous:
            execute_discipline(job.id, engine)

        timer = time.time()

        return get_job_from_id(
            job.id,
            data_type=DataType.json,
            long_polling=False,
            engine=engine,
            timer=timer,
        )
