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

"""A discipline to execute remote GEMSEO processes through HTTP."""

from __future__ import annotations

import time
from collections.abc import Iterable
from hashlib import sha256
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import numpy
from gemseo.core.discipline import Discipline
from gemseo.utils.constants import READ_ONLY_EMPTY_DICT
from gemseo.utils.directory_creator import DirectoryCreator
from gemseo.utils.directory_creator import DirectoryNamingMethod
from httpx import Client

from _gemseo_http_common.constants import ExecutionMode as _ExecutionMode
from _gemseo_http_common.data_conversion import convert_dict_array_to_list
from _gemseo_http_common.data_conversion import convert_dict_list_to_array
from _gemseo_http_common.database import File
from _gemseo_http_common.database import Job
from _gemseo_http_common.database import JobStatus
from _gemseo_http_common.models import DisciplineOptions
from _gemseo_http_common.models import ExecuteInput
from gemseo_http._data_conversion import convert_dict_of_dict_list_to_array
from gemseo_http._files import compute_sha256sum
from gemseo_http._files import flatten_file_paths

if TYPE_CHECKING:
    from collections.abc import Mapping
    from collections.abc import Sequence

    from gemseo.typing import StrKeyMapping
    from numpy.typing import NDArray

LOGGER = getLogger(__name__)


class HTTPDiscipline(Discipline):
    """A discipline to execute a remote GEMSEO process exposed as an HTTP service."""

    ExecutionMode = _ExecutionMode
    """The execution mode."""

    __is_asynchronous: bool
    """Whether the execution mode is asynchronous."""

    __discipline_options: dict[str, Any]
    """The arguments passed to the discipline constructor."""

    __domain_port: str
    """The domain port of the service."""

    __file_paths_to_upload: tuple[Path, ...]
    """The paths of the files to upload before execution."""

    __file_paths_to_download: tuple[Path, ...]
    """The paths of the files to download after execution."""

    __linearize_after_execution: bool
    """Whether to linearize after execute."""

    __linearize_options: dict[str, Any]
    """The arguments passed to linearize."""

    __use_long_polling: bool
    """Whether to use long polling in asynchronous mode."""

    __polling_wait_time: float
    """The wait time in case of polling"""

    __execution_timeout: int
    """The maximum execution time in seconds."""

    __chunk_size: int
    """The size of the chunks to upload the files."""

    def __init__(
        self,
        name: str,
        class_name: str,
        url: str,
        port: int = 443,
        user: str = "",
        password: str = "",
        token: str = "",
        discipline_options: dict[str, Any] = READ_ONLY_EMPTY_DICT,
        is_asynchronous: bool = False,
        root_path: str | Path = "",
        directory_naming_method: DirectoryNamingMethod = DirectoryNamingMethod.NUMBERED,
        inputs_to_upload: Iterable[str] = (),
        outputs_to_download: Iterable[str] = (),
        file_paths_to_upload: Iterable[str | Path] = (),
        file_paths_to_download: Iterable[str | Path] = (),
        httpx_client_options: dict[str, Any] = READ_ONLY_EMPTY_DICT,
        use_long_polling: bool = True,
        polling_wait_time: float = 10.0,
        linearize_after_execution: bool = False,
        linearize_options: dict[str, Any] = READ_ONLY_EMPTY_DICT,
        http_client: Client = None,
        execution_timeout: int = 3600 * 5,
        chunk_size: int = 1024 * 1000,
    ) -> None:
        """
        Args:
            class_name: The name of the remote discipline class.
            url: The URL of the service.
            port: The port of the service.
            user: The user's name, only used if token is not set.
            password: The user's password, only used if token is not set.
            token: An access token, if any.
            discipline_options: The arguments passed to the discipline constructor.
            is_asynchronous: Whether to perform the remote computations
                in background in an async manner.
            root_path: The path to the root directory.
            directory_naming_method: The method used to name the created directories.
            inputs_to_upload: The names of the discipline inputs that correspond
                to files that must be uploaded before execution.
            outputs_to_download: The names of the discipline outputs that correspond
                to files that must be downloaded after execution.
            file_paths_to_upload: The paths of the files to upload before execution.
            file_paths_to_download: The paths of the files to download after execution.
            httpx_client_options: The arguments passed to the httpx client constructor.
            use_long_polling: Whether to use long polling in asynchronous mode.
            polling_wait_time: The wait time in case of polling.
            linearize_after_execution: Whether to linearize after execute.
            linearize_options: The arguments passed to linearize.
            http_client: A HTTP client that can be injected
             (for testing purposes or custom network configuration).
            execution_timeout: The maximum execution time in seconds.
            chunk_size: The size of the chunks to upload the files.
        """  # noqa: D205, D212, D415
        self.__is_asynchronous = is_asynchronous
        self.__linearize_after_execution = linearize_after_execution
        self.__linearize_options = linearize_options

        self._http_client = http_client or Client(**httpx_client_options)

        self.__discipline_options = discipline_options

        self.__domain_port = f"{url}:{port}"
        self.__execute_endpoint = f"/v1/discipline/{class_name}/execute"

        self.__inputs_to_upload = inputs_to_upload
        self.__outputs_to_download = outputs_to_download

        self.__file_paths_to_upload = tuple(map(Path, file_paths_to_upload))
        self.__file_paths_to_download = tuple(map(Path, file_paths_to_download))

        self.__directory_creator = DirectoryCreator(root_path, directory_naming_method)

        if not token:
            token = self.__authenticate(user, password)

        self._http_client.headers.update({"Authorization": f"Bearer {token}"})

        self.__use_long_polling = use_long_polling
        self.__polling_wait_time = polling_wait_time

        self.__execution_timeout = execution_timeout
        self.__chunk_size = chunk_size

        super().__init__(name=name)
        self.input_grammar.update_from_schema(
            self.__get_grammar_schema(class_name, "inputs")
        )
        self.output_grammar.update_from_schema(
            self.__get_grammar_schema(class_name, "outputs")
        )

        self.__set_default_input_data(class_name)

    def __set_default_input_data(self, class_name: str) -> None:
        """Set the default input data.

        Args:
            class_name: The name of the remote discipline class.

        Raises:
            RuntimeError: If the request has failed with a given error.
        """
        response = self._http_client.post(
            f"/v1/discipline/{class_name}/default_input_data",
            json=DisciplineOptions(
                discipline_options=self.__discipline_options
            ).model_dump(),
        )
        if response.status_code != 200:
            msg = (
                "Error while fetching the default input data."
                f"The status code is {response.status_code}"
                f" with the message: {response.text}."
            )
            raise ConnectionError(msg)
        self.io.input_grammar.defaults = convert_dict_list_to_array(response.json())

    def __authenticate(self, user: str, password: str) -> str:
        """Authenticate the user.

        Args:
            user: The user.
            password: The password.

        Returns:
            The token.
        """
        data = {"username": user, "password": password}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        request = self._http_client.post(
            f"{self.__domain_port}/token",
            data=data,
            headers=headers,
        )
        if request.status_code != 200:
            msg = (
                "Cannot obtain a token with the current login/password."
                f"Request ended with {request.status_code}."
            )
            raise ConnectionError(msg)
        token = request.json()["access_token"]
        LOGGER.debug("Authentication successful.")
        LOGGER.debug("Access token: %s", token)
        return token

    def __get_grammar_schema(
        self,
        class_name: str,
        schema_prefix: str,
    ) -> dict[str, Any]:
        """Return the schema for a JSON grammar.

        Args:
            class_name: The name of the remote discipline class.
            schema_prefix: The prefix for the schema endpoint.

        Returns:
            The schema.

        Raises:
            RuntimeError: The request has failed with a given error.
        """
        endpoint = (
            f"{self.__domain_port}/v1/discipline/{class_name}/{schema_prefix}_schema"
        )
        discipline_options = DisciplineOptions(
            discipline_options=dict(self.__discipline_options)
        ).model_dump()
        request = self._http_client.post(endpoint, json=discipline_options)
        if request.status_code != 200:
            msg = (
                f"Request {endpoint} failed with error code {request.status_code}."
                f" The remote error is: {request.json()['detail']}: "
            )
            raise RuntimeError(msg)

        schema = request.json()
        LOGGER.debug("Schema for %s: %s", schema_prefix, schema)
        return schema

    def __upload_files(self) -> list[File]:
        """Upload all the files.

        Returns:
            The schemas of the uploaded files.
        """
        file_paths = self.__file_paths_to_upload + tuple(
            Path(self.local_data[key]) for key in self.__inputs_to_upload
        )

        LOGGER.debug("Uploading files to the server...")

        endpoint = f"{self.__domain_port}/v1/file/upload"
        remote_file_schemas = []

        for file_path in file_paths:
            nb_chunks, remaining_size = divmod(
                file_path.stat().st_size, self.__chunk_size
            )
            chunk_sizes = [self.__chunk_size] * nb_chunks + [remaining_size]
            nb_chunks += 1
            with file_path.open("rb") as file_handler:
                # TODO: handle empty files.
                for i, chunk_size in enumerate(chunk_sizes):
                    data = {"total_chunks": nb_chunks, "chunk_number": i}
                    files = {"files": (file_path.name, file_handler.read(chunk_size))}
                    req = self._http_client.post(endpoint, files=files, data=data)
                    if req.status_code != 200:
                        msg = f"Failed to upload the file: {req.status_code}."
                        raise RuntimeError(msg)
                remote_file_schema = File(**req.json()[0])
                remote_file_schemas.append(remote_file_schema)
                LOGGER.debug("File %s uploaded.", file_path)
                LOGGER.debug("File %s details: %s", file_path, remote_file_schema)

        self.__check_file_hashes(file_paths, remote_file_schemas)

        return remote_file_schemas

    def __check_file_hashes(
        self,
        file_paths: Sequence[str | Path],
        remote_file_schemas: Sequence[File],
    ) -> None:
        """Check the file hashes of local files against provided remote file schemas.

        Args:
            file_paths : The file paths to the local files whose hashes
                need to be validated.
            remote_file_schemas: The file schemas containing the expected
                SHA-256 hashes against which the local file hashes are compared.

        Raises:
            ValueError: If a file's calculated hash does not match the expected hash.
        """
        _, file_hashes = self.__get_file_hashes(file_paths)
        for hash_, schema, path in zip(
            file_hashes, remote_file_schemas, file_paths, strict=False
        ):
            if schema.sha256sum != hash_:
                msg = (
                    "File hash mismatch for %s: %s != %s",
                    path,
                    schema.sha256sum,
                    hash_,
                )
                raise ValueError(msg)
        LOGGER.debug("File hashes OK.")

    def __download_files(
        self,
        job_id: int,
        output_data: StrKeyMapping,
    ) -> None:
        """Download the files of a job.

        Args:
            job_id: The job id.
            output_data: The output data from the server.

        Raises:
            ValueError: If a file bound to a variable is not correct.
        """
        if not (self.__outputs_to_download or self.__file_paths_to_download):
            return

        LOGGER.debug("Downloading the files...")

        directory_path = self.__directory_creator.create()

        output_paths_to_download = []
        for name in self.__outputs_to_download:
            value = output_data[name]
            if isinstance(value, str):
                path = Path(value)
                output_paths_to_download.append(path)
                new_value = str(directory_path / path)
            elif isinstance(value, Iterable) and not isinstance(value, numpy.ndarray):
                output_paths_to_download += map(Path, value)
                new_value = [str(directory_path / Path(val)) for val in value]
            else:
                msg = f"Wrong type for the variable holding a file: {value}"
                raise TypeError(msg)
            output_data[name] = new_value

        # Retrieve all the remote files for the current job.
        job_url = f"{self.__domain_port}/v1/job/{job_id}"
        endpoint = f"{job_url}/files"
        r = self._http_client.get(endpoint)
        remote_files_and_directories = r.json()

        # Transfer output names may contain directory or subdirectories.
        # Walk these directories and detect all the files inside them to be downloaded.
        file_paths_to_download = []
        for path in self.__file_paths_to_download:
            file_paths_to_download += flatten_file_paths(
                path, remote_files_and_directories
            )

        for file_path in set(file_paths_to_download + output_paths_to_download):
            endpoint = f"{job_url}/files/download?filename={file_path}"
            with self._http_client.stream("GET", endpoint) as r:
                r.raise_for_status()
                complete_path = Path(directory_path) / Path(file_path)
                parent = complete_path.parent
                parent.mkdir(parents=True, exist_ok=True)
                with complete_path.open("wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
                LOGGER.debug(
                    "File %s downloaded to the full path %s.", file_path, complete_path
                )

    @staticmethod
    def __get_file_hashes(file_paths: Iterable[Path]) -> tuple[str, list[str]]:
        """Compute the hash keys for the files.

        Args:
            file_paths: The file paths.

        Returns:
            The global hash and the file's hashes.
        """
        file_hashes = []
        global_hash = sha256()
        for file_path in file_paths:
            file_hash = compute_sha256sum(file_path)
            file_hashes.append(file_hash)
            global_hash.update(file_hash.encode())
        LOGGER.debug("Files hash keys: %s", file_hashes)
        LOGGER.debug("Global hash key: %s", global_hash)
        return global_hash.hexdigest(), file_hashes

    def __execute_on_remote(
        self,
        input_files: list[File],
        input_data: Mapping[str, Any],
    ) -> Job:
        """Execute the discipline remotely.

        Args:
            input_files: The input file schemas.
            input_data: The input data.

        Returns:
            The request job.
        """
        converted_input_data = convert_dict_array_to_list(input_data)
        execute_inputs = ExecuteInput(
            name=self.name,
            discipline_options=self.__discipline_options,
            input_files=input_files,
            input_data=converted_input_data,
            linearize=self.__linearize_after_execution,
            linearize_options=self.__linearize_options,
            linearization_mode=self._linearization_mode,
            differentiated_inputs=self._differentiated_input_names,
            differentiated_outputs=self._differentiated_output_names,
        )

        execution_mode = (
            self.ExecutionMode.asynchronous
            if self.__is_asynchronous
            else self.ExecutionMode.synchronous
        )
        request = self._http_client.post(
            f"{self.__domain_port}{self.__execute_endpoint}?execution_mode={execution_mode}",
            json=execute_inputs.model_dump(),
        )

        if request.status_code not in (200, 202):
            msg = (
                "Something went wrong while calling the server."
                " Please contact the server administrator."
            )
            raise RuntimeError(msg)

        job = Job(**request.json())

        LOGGER.debug("Job %s submitted to the server.", job.id)
        return job

    def __get_finished_job(self, job: Job) -> Job:
        """Return the output data from the remote.

        Args:
            job: The job.

        Returns:
            The output data.

        Raises:
            RuntimeError: If the timeout is reached.
        """
        if not self.__is_asynchronous:
            if job.job_status != JobStatus.finished:
                LOGGER.info("Job %s failed. Remote traceback below:", job.id)
                raise RuntimeError(job.traceback)
            return job

        initial_time = time.time()
        LOGGER.debug("Using long-polling: %s", self.__use_long_polling)
        LOGGER.debug(
            "The polling timeout is set to %s seconds.", self.__polling_wait_time
        )
        while True:
            job = self.__poll_job(job.id)

            if job.job_status in (JobStatus.finished.value, JobStatus.failed.value):
                break

            elapsed_time = time.time() - initial_time
            if elapsed_time > self.__execution_timeout:
                msg = f"Execution time exceeded {self.__execution_timeout}s."
                raise RuntimeError(msg)
            if not self.__use_long_polling:
                LOGGER.debug(
                    "Waiting %s seconds before polling.", self.__polling_wait_time
                )
                time.sleep(self.__polling_wait_time)

        if job.job_status == JobStatus.failed.value:
            LOGGER.info("Job %s failed. Remote traceback below:", job.id)
            raise RuntimeError(job.traceback)

        return job

    def __poll_job(self, job_id: int) -> Job:
        """Poll the server for the job status.

        Args:
             job_id: The job id.

        Returns:
            The job.
        """
        LOGGER.debug("Polling the server for job %s...", job_id)
        start_polling = time.time()
        endpoint = (
            f"{self.__domain_port}/v1/job/{job_id}?"
            f"long_polling={self.__use_long_polling}"
            f"&long_polling_timeout={self.__polling_wait_time}"
        )
        request = self._http_client.get(endpoint)
        elapsed_time = time.time() - start_polling
        LOGGER.debug("Polling the server done in %s", elapsed_time)
        return Job(**request.json())

    def _run(self, input_data: StrKeyMapping) -> StrKeyMapping:
        input_files = self.__upload_files()

        # The local files are converted to their name only,
        # as their absolute path is not relevant remotely.
        # A corollary is that the remote discipline should access the files
        # at their root directory level.
        for name in self.__inputs_to_upload:
            input_data[name] = Path(input_data[name]).name

        job = self.__execute_on_remote(input_files, input_data)

        job = self.__get_finished_job(job)
        output_data = convert_dict_list_to_array(job.output_data)
        self.__download_files(job.id, output_data)

        if self.__linearize_after_execution:
            self.jac = convert_dict_of_dict_list_to_array(job.jacobian_data)
            self._is_linearized = True

        return output_data

    def linearize(  # noqa: D102
        self,
        input_data: Mapping[str, Any] | None = None,
        compute_all_jacobians: bool = False,
        execute: bool = True,
    ) -> Mapping[str, Mapping[str, NDArray[float]]]:
        self.__linearize_options = {
            "compute_all_jacobians": compute_all_jacobians,
            "execute": execute,
        }
        self.__linearize_after_execution = True
        return super().linearize(input_data, compute_all_jacobians)
