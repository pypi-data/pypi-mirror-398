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

"""GEMSEO HTTP Web application."""

from __future__ import annotations

import shutil
import time
from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks  # noqa: TC002
from fastapi import Depends
from fastapi import FastAPI
from fastapi import File as FastAPIFile
from fastapi import Form
from fastapi import HTTPException
from fastapi import Response  # noqa: TC002
from fastapi import UploadFile  # noqa: TC002
from fastapi import status
from fastapi.responses import FileResponse  # noqa:TC002
from fastapi.security import OAuth2PasswordRequestForm  # noqa:TC002
from gemseo import configure
from gemseo import create_discipline
from gemseo import get_available_disciplines
from gemseo import get_discipline_inputs_schema as _get_discipline_inputs_schema
from gemseo import get_discipline_outputs_schema as _get_discipline_outputs_schema
from gemseo.core.discipline import Discipline  # noqa: TC002
from sqlalchemy import Engine
from sqlmodel import Session
from sqlmodel import select

from _gemseo_http_common.constants import ExecutionMode
from _gemseo_http_common.data_conversion import convert_dict_array_to_list
from _gemseo_http_common.database import File
from _gemseo_http_common.database import Job
from _gemseo_http_common.models import DisciplineOptions  # noqa: TC001
from _gemseo_http_common.models import ExecuteInput  # noqa: TC001
from gemseo_http_server.database import User
from gemseo_http_server.database import create_engine
from gemseo_http_server.job_creation import DataType
from gemseo_http_server.job_creation import create_job_in_database
from gemseo_http_server.job_creation import download_file_from_job_id
from gemseo_http_server.job_creation import get_file_paths
from gemseo_http_server.job_creation import get_job_from_id
from gemseo_http_server.job_creation import get_jobs_for_user
from gemseo_http_server.models import Token
from gemseo_http_server.security import authenticate_user
from gemseo_http_server.security import create_token
from gemseo_http_server.security import get_current_active_user
from gemseo_http_server.settings import settings
from gemseo_http_server.utils import compute_sha256sum
from gemseo_http_server.utils import load_users_from_db

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlalchemy import Engine


configure(
    enable_discipline_statistics=settings.enable_discipline_counters,
    enable_discipline_cache=settings.enable_discipline_cache,
    enable_progress_bar=settings.enable_progress_bar,
    enable_function_statistics=settings.enable_function_counters,
)


app = FastAPI(debug=settings.fastapi_debug)
app.openapi_version = settings.openapi_version


def get_discipline_from_name(
    discipline_name: str,
    body: DisciplineOptions | None = None,
) -> Discipline:
    """Return a discipline based on its name.

    This function attempts to find and return a discipline entity by looking up
    the provided discipline name in the list of available disciplines. If the
    discipline name is not found, an HTTPException is raised with a 404 status code.

    Args:
        discipline_name: The name of the discipline class.
        body: The discipline options.

    Returns:
        The discipline instance.

    Raises:
        HTTPException: If the discipline name is not found in the list
            of available disciplines.
    """
    discipline_options = body.discipline_options if body else {}
    try:
        return create_discipline(discipline_name, **discipline_options)
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg
        ) from exc


@app.post("/token", response_model=Token)
def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    engine: Engine = Depends(create_engine),  # noqa: B008
) -> dict[str, str]:
    """Return a token after a user/password authentication.

    Args:
        form_data: The form input data.
        engine: The database engine.

    Returns:
        The access token info.
    """
    users_db = load_users_from_db(engine)
    user = authenticate_user(users_db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_token(data={"sub": user.username}, expires_delta=token_expires_delta)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/v1/user/me/", response_model=User)
def get_user(
    user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Return the information for the logged user.

    Args:
        user: A dependency injection to enforce the login of the current user.

    Returns:
        The current user.
    """
    return user


@app.get("/v1/discipline")
def get_disciplines(
    user: Annotated[User, Depends(get_current_active_user)],
) -> list[str]:
    """Return the available disciplines.

    Args:
        user: The current user logged in.

    Return:
        The available disciplines.
    """
    return get_available_disciplines()


@app.post("/v1/discipline/{discipline_name}/input_names")
def get_discipline_input_names(
    discipline_name: str,
    user: Annotated[User, Depends(get_current_active_user)],
    discipline: Annotated[Discipline, Depends(get_discipline_from_name)],
    body: DisciplineOptions | None = None,
) -> list[str]:
    """Return the input names of a discipline.

    Args:
        discipline_name: The name of the discipline.
        user: The current user logged in.
        body: The input body.

    Returns:
        The input names of the discipline.
    """
    return discipline.io.input_grammar.names


@app.post("/v1/discipline/{discipline_name}/inputs_schema")
def get_discipline_inputs_schema(
    discipline_name: str,
    user: Annotated[User, Depends(get_current_active_user)],
    discipline: Annotated[Discipline, Depends(get_discipline_from_name)],
    body: DisciplineOptions | None = None,
) -> dict[Any, Any]:
    """Return the inputs schema of a discipline.

    Args:
         discipline_name: The name of the discipline.
         discipline: The discipline instance.
         user: The current user logged in.
         body: The body of the POST request.

    Returns:
        The input grammar schema of the discipline.
    """
    return _get_discipline_inputs_schema(discipline)


@app.post("/v1/discipline/{discipline_name}/output_names")
def get_discipline_output_names(
    discipline_name: str,
    user: Annotated[User, Depends(get_current_active_user)],
    discipline: Annotated[Discipline, Depends(get_discipline_from_name)],
    body: DisciplineOptions | None = None,
) -> list[str]:
    """Return the output names of a discipline.

    Args:
         discipline_name: The name of the discipline.
         user: The current user logged in.
         discipline: The discipline instance.
         body: The body of the POST request.

    Returns:
        The output names of the discipline.
    """
    return discipline.io.output_grammar.names


@app.post("/v1/discipline/{discipline_name}/outputs_schema")
def get_discipline_outputs_schema(
    discipline_name: str,
    user: Annotated[User, Depends(get_current_active_user)],
    discipline: Annotated[Discipline, Depends(get_discipline_from_name)],
    body: DisciplineOptions | None = None,
) -> dict[Any, Any]:
    """Return the outputs schema of a discipline.

    Args:
        discipline_name: The name of the discipline.
        response: The HTTP response to the client.
        user: The current user logged in.
        discipline: The discipline instance.
        body: The input body.

    Returns:
        The outputs schema of the discipline.
    """
    return _get_discipline_outputs_schema(discipline)


@app.post("/v1/discipline/{discipline_name}/default_input_data")
def get_discipline_default_inputs(
    discipline_name: str,
    user: Annotated[User, Depends(get_current_active_user)],
    discipline: Annotated[Discipline, Depends(get_discipline_from_name)],
    body: DisciplineOptions | None = None,
) -> Mapping[Any, Any]:
    """Return the default input data of a discipline.

    Args:
        discipline_name: The name of the discipline.
        user: The current user logged in.
        discipline: The discipline instance.
        body: The input body.

    Returns:
        The default input data for the discipline with its given options.
    """
    return convert_dict_array_to_list(discipline.default_input_data)


@app.post("/v1/discipline/{discipline_name}/execute", response_model=str | Job)
def execute_discipline(
    discipline_name: str,
    user: Annotated[User, Depends(get_current_active_user)],
    discipline: Annotated[Discipline, Depends(get_discipline_from_name)],
    background_task: BackgroundTasks,
    response: Response,
    body: ExecuteInput | None = None,
    execution_mode: ExecutionMode = ExecutionMode.synchronous,
    engine: Engine = Depends(create_engine),  # noqa: B008
) -> Response | Job:
    """Execute a discipline.

    Execute on the server side the discipline with the payload provided by the user.

    Args:
        discipline_name: The discipline name to execute.
        user: The current user logged in.
        background_task: Provides functionality to execute the job in the background,
            enabling asynchronous processing.
        response: Represents the HTTP response,
            used for providing status updates or custom responses to the client.
        body: The body of the POST request containing the details of the discipline
            to execute.
        execution_mode: Determines the execution type,
            either synchronous (immediate output) or asynchronous (background job).
        engine: The database engine.

    Returns:
        Either the output data, or the job id, depending on the query type.
    """
    return create_job_in_database(
        user,
        discipline_name,
        body,
        engine,
        execution_mode,
        background_task,
        response,
    )


@app.get("/v1/job", response_model=list[Job])
def get_jobs(
    user: Annotated[User, Depends(get_current_active_user)],
    engine: Engine = Depends(create_engine),  # noqa: B008
) -> list[Job]:
    """Return the jobs of a user.

    Args:
        user: The current user logged in.
        engine: The database engine.

    Returns:
        The jobs of the user and their states.
    """
    return get_jobs_for_user(user.id, engine)


@app.get("/v1/job/{job_id}", response_model=Job)
def get_job(
    job_id: int,
    user: Annotated[User, Depends(get_current_active_user)],
    data_type: DataType = DataType.json,
    long_polling: bool = False,
    long_polling_timeout: int = 100,
    engine: Engine = Depends(create_engine),  # noqa: B008
) -> Job:
    """Return the job.

    Execute on the server side the discipline with the payload provided by the user.

    Args:
        job_id: The discipline name to execute.
        user: The current user logged in.
        data_type: The datatype used for serialization.
        long_polling: Whether to use long polling.
        long_polling_timeout: The long polling timeout.
        engine: The database engine.

    Returns:
        The output data to the client.
    """
    return get_job_from_id(
        job_id, data_type, long_polling, time.time(), engine, long_polling_timeout
    )


@app.get("/v1/job/{job_id}/files", response_model=dict[str, Any] | str)
def get_job_files(
    job_id: str,
    user: Annotated[User, Depends(get_current_active_user)],
    response: Response,
    engine: Engine = Depends(create_engine),  # noqa: B008
) -> dict[str, Any] | str:
    """Return the files of a job.

    Args:
        job_id: The discipline name to execute.
        user: The current user logged in.
        response: The response.
        engine: The database engine.

    Returns:
        The directory tree of the job.
    """
    return get_file_paths(user.id, job_id, response, engine)


@app.get("/v1/job/{job_id}/files/download")
def get_job_file(
    job_id: str,
    user: Annotated[User, Depends(get_current_active_user)],
    response: Response,
    filename: str,
    engine: Engine = Depends(create_engine),  # noqa: B008
) -> FileResponse:
    """Return a file of a job.

    Args:
        job_id: The discipline name to execute.
        user: The current user logged in.
        response: The response.
        filename: The filename to download.
        engine: The database engine.

    Returns:
        The file response.
    """
    return download_file_from_job_id(user.id, job_id, response, filename, engine)


@app.get("/v1/file", response_model=Sequence[File])
def get_files_on_server(
    user: Annotated[User, Depends(get_current_active_user)],
    engine: Engine = Depends(create_engine),  # noqa: B008
) -> Sequence[File] | str:
    """Return the user's files on the server.

    Args:
         user: The current user.
         engine: The database engine.
    """
    with Session(engine) as session:
        statement = select(File).where(File.user_id == user.id)
        return session.exec(statement).all()


@app.post("/v1/file/upload", response_model=list[File] | str)
def upload_files_on_server(
    user: Annotated[User, Depends(get_current_active_user)],
    files: list[UploadFile] = FastAPIFile(...),  # noqa: B008
    chunk_number: int = Form(0),
    total_chunks: int = Form(1),
    engine: Engine = Depends(create_engine),  # noqa: B008
) -> list[File] | str:
    """Upload files on the server.

    Args:
        user: The current user.
        files: The files to upload.
        chunk_number: The current chunk number.
        total_chunks: The total number of chunks.
        engine: The database engine.

    Returns:
        The files or a strings if a chunk has been uploaded.
    """
    user_file_directory = Path(settings.user_file_directory)
    files_db = []
    is_last = (int(chunk_number) + 1) == int(total_chunks)
    chunk_directory = user_file_directory / "chunks"
    for file in files:
        filename = f"{file.filename}_{chunk_number}"
        file_location = chunk_directory / filename
        with file_location.open("wb+") as f:
            shutil.copyfileobj(file.file, f)
        if is_last:
            unique_filename = str(uuid4())
            file_location = user_file_directory / unique_filename
            with file_location.open("wb") as buffer:
                chunk = 0
                while chunk < total_chunks:
                    chunk_path = chunk_directory / f"{file.filename}_{chunk}"
                    with chunk_path.open("rb") as f_chunk:
                        buffer.write(
                            f_chunk.read()
                        )  # Write the chunk to the final file
                    chunk_path.unlink()
                    chunk += 1
            file_db_entry = File(
                filename=file.filename,
                unique_filename=unique_filename,
                sha256sum=compute_sha256sum(file_location),
                user_id=user.id,
            )
            files_db.append(file_db_entry)
            with Session(engine) as session:
                session.add(file_db_entry)
                session.commit()
                session.refresh(file_db_entry)

    if is_last:
        return files_db
    return "Chunks uploaded"
