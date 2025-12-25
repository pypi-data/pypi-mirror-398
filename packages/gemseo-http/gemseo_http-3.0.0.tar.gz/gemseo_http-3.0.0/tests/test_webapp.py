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

from filecmp import cmp
from os import makedirs
from pathlib import Path

import pytest
from gemseo import create_discipline
from gemseo import get_available_disciplines
from gemseo.core.discipline import Discipline
from numpy import array
from numpy.testing import assert_equal

from _gemseo_http_common.constants import ExecutionMode
from _gemseo_http_common.data_conversion import convert_dict_array_to_list
from _gemseo_http_common.data_conversion import convert_dict_list_to_array
from _gemseo_http_common.data_conversion import convert_dict_of_dict_array_to_list
from _gemseo_http_common.database import Job
from _gemseo_http_common.database import JobStatus
from _gemseo_http_common.models import DisciplineOptions
from _gemseo_http_common.models import ExecuteInput
from gemseo_http._files import flatten_file_paths
from gemseo_http._files import show_directory_tree
from gemseo_http_server.app import settings
from tests.conftest import FAKE_USER

DIR_PATH = Path(__file__).parent.resolve()


def test_get_token_valid_user_valid_password(test_client):
    """Check that a valid user and password lead to a valid token."""
    data = {"username": "test", "password": "test"}
    response = test_client.post("/token", data=data)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_token_valid_user_wrong_password(test_client):
    """Check that a valid user and password lead to a valid token."""
    data = {"username": "test", "password": "wrongpassword"}
    response = test_client.post("/token", data=data)
    assert response.status_code == 401


def test_get_token_wrong_user_wrong_password(test_client):
    """Check that a wrong user and password leads a 401 unauthorized message."""
    data = {"username": "test", "password": "wrongpassword"}
    response = test_client.post("/token", data=data)
    assert response.status_code == 401


def test_get_current_user(test_client, fake_current_active_user):
    """Check that the server sends the list of disciplines."""
    response = test_client.get("/v1/user/me")
    assert response.json() == FAKE_USER.model_dump()


def test_get_disciplines(test_client, fake_current_active_user):
    """Check that the server sends the list of disciplines."""
    response = test_client.get("/v1/discipline")
    assert response.json() == get_available_disciplines()


def test_upload_file_and_query_file(test_client, fake_current_active_user):
    file_path = DIR_PATH / "data" / "test.pdf"
    with Path(file_path).open("rb") as file_handler:
        req = test_client.post("/v1/file/upload", files=[("files", file_handler)])
    data = req.json()
    assert cmp(
        file_path,
        settings.user_file_directory / data[0]["unique_filename"],
        shallow=False,
    )

    req = test_client.get("/v1/file")
    data_2 = req.json()
    assert data_2[0] == data[0]


@pytest.mark.parametrize("nb_chunks", [1, 2, 3, 4, 5])
def test_upload_file_chunks(test_client, fake_current_active_user, nb_chunks):
    file_path = DIR_PATH / "data" / "test.pdf"
    file_size = file_path.stat().st_size
    chunk_size = file_size // nb_chunks
    chunk_size_rest = file_size % nb_chunks
    chunks_size = [chunk_size] * nb_chunks
    chunks_size[-1] += chunk_size_rest
    with Path(file_path).open("rb") as file_handler:
        for i in range(nb_chunks):
            form_data = {"total_chunks": nb_chunks, "chunk_number": i}
            data = file_handler.read(chunks_size[i])
            files = {"files": (file_path.name, data)}
            req = test_client.post("/v1/file/upload", files=files, data=form_data)
            data = req.json()
    assert cmp(
        file_path,
        settings.user_file_directory / data[0]["unique_filename"],
        shallow=False,
    )


@pytest.mark.parametrize("discipline", ["Sellar1", "SobieskiMission"])
def test_discipline_inputs(discipline, test_client, fake_current_active_user):
    """Test to get the discipline inputs via the webapp."""
    response = test_client.post(f"/v1/discipline/{discipline}/input_names")
    discipline = create_discipline(discipline)
    assert response.json() == list(discipline.io.input_grammar.names)


@pytest.mark.parametrize("discipline", ["Sellar1", "SobieskiMission"])
def test_discipline_default_inputs(discipline, test_client, fake_current_active_user):
    """Test to get the discipline default input data via the webapp."""
    response = test_client.post(f"/v1/discipline/{discipline}/default_input_data")
    discipline = create_discipline(discipline)
    data = response.json()
    default_inputs = convert_dict_list_to_array(data)
    for key in data:
        assert_equal(data[key], default_inputs[key])


def test_discipline_inputs_with_parameters(test_client, fake_current_active_user):
    """Test to get the discipline inputs via the webapp."""
    discipline = "AnalyticDiscipline"
    expressions = {"expressions": {"y_1": "2*x**2", "y_2": "4*x**2+5+z**3"}}
    discipline_options = DisciplineOptions(discipline_options=expressions)
    json = discipline_options.model_dump()
    response = test_client.post(f"/v1/discipline/{discipline}/input_names", json=json)
    discipline = create_discipline(discipline, **expressions)
    assert response.json() == list(discipline.io.input_grammar.names)


@pytest.mark.parametrize("discipline", ["Sellar1", "SobieskiMission"])
def test_discipline_outputs(discipline, test_client, fake_current_active_user):
    """Test to get the discipline outputs via the webapp."""
    response = test_client.post(f"/v1/discipline/{discipline}/output_names")
    discipline = create_discipline(discipline)
    assert response.json() == list(discipline.io.output_grammar.names)


@pytest.mark.parametrize(
    "grammar", ["input_names", "inputs_schema", "output_names", "outputs_schema"]
)
def test_discipline_grammar_unknown_discipline(
    test_client, fake_current_active_user, grammar
):
    """Test to get the discipline outputs via the webapp."""
    response = test_client.post(f"/v1/discipline/not_a_discipline/{grammar}")
    assert response.status_code == 404
    assert "The class not_a_discipline is not available;" in response.text


def test_discipline_unknown_discipline(test_client, fake_current_active_user):
    """Test to get the discipline outputs via the webapp."""
    response = test_client.post("/v1/discipline/not_a_discipline/execute")
    assert response.status_code == 404
    assert "The class not_a_discipline is not available;" in response.text


def test_discipline_outputs_with_parameters(test_client, fake_current_active_user):
    """Test to get the discipline inputs via the webapp."""
    discipline = "AnalyticDiscipline"
    expressions = {"expressions": {"y_1": "2*x**2", "y_2": "4*x**2+5+z**3"}}
    discipline_options = DisciplineOptions(discipline_options=expressions)
    json = discipline_options.model_dump()
    response = test_client.post(f"/v1/discipline/{discipline}/output_names", json=json)
    discipline = create_discipline(discipline, **expressions)
    assert response.json() == list(discipline.io.output_grammar.names)


def test_discipline_execution_no_data(tmp_path, test_client, fake_current_active_user):
    """Test the discipline execution endpoint with no input data."""
    synchronous = ExecutionMode.synchronous.value
    response = test_client.post(
        f"/v1/discipline/Sellar1/execute?execution_mode={synchronous}"
    )
    assert response.status_code == 200
    discipline = create_discipline("Sellar1")
    out_discipline = discipline.execute()
    converted_response = convert_dict_list_to_array(response.json()["output_data"])
    for key in out_discipline:
        assert out_discipline[key] == pytest.approx(converted_response[key])


def test_discipline_execution_sellar1(tmp_path, test_client, fake_current_active_user):
    """Test the discipline execution with the Sellar1 and input data."""
    data = {"x_shared": array([0.0, 1.0]), "y_2": array([2.0])}
    input_data = convert_dict_array_to_list(data)
    data_model = ExecuteInput()
    data_model.input_data = input_data

    synchronous = ExecutionMode.synchronous.value
    response = test_client.post(
        f"/v1/discipline/Sellar1/execute?execution_mode={synchronous}",
        json=data_model.model_dump(),
    )
    output_data_remote = convert_dict_list_to_array(response.json()["output_data"])

    discipline = create_discipline("Sellar1")
    output_data = discipline.execute(data)
    for key in output_data:
        assert output_data[key] == pytest.approx(output_data_remote[key])


def test_discipline_execution_parametric_discipline(
    tmp_path, test_client, fake_current_active_user
):
    """Test the discipline execution with the Sellar1 and input data."""
    expressions = {"expressions": {"y_1": "2*x**2", "y_2": "4*x**2+5+z**3"}}
    data = {"x": [1.0], "z": [2.0]}
    data_model = ExecuteInput()
    data_model.input_data = data
    data_model.discipline_options = expressions

    synchronous = ExecutionMode.synchronous.value
    response = test_client.post(
        f"/v1/discipline/AnalyticDiscipline/execute?execution_mode={synchronous}",
        json=data_model.model_dump(),
    )
    output_data = response.json()["output_data"]

    discipline = create_discipline("AnalyticDiscipline", **expressions)
    out_discipline = discipline.execute(convert_dict_list_to_array(data))

    assert output_data["y_1"] == pytest.approx(out_discipline["y_1"])
    assert output_data["y_2"] == pytest.approx(out_discipline["y_2"])


def test_discipline_execution_failing_parametric_discipline(
    tmp_path, test_client, fake_current_active_user
):
    """Test the discipline execution with the Sellar1 and input data."""
    expressions = {"expressions": {"y_1": "1/x", "y_2": "4*x**2+5+z**3"}}
    data = {"x": [0.0], "z": [2.0]}
    data_model = ExecuteInput()
    data_model.input_data = data
    data_model.discipline_options = expressions

    synchronous = ExecutionMode.synchronous.value
    response = test_client.post(
        f"/v1/discipline/AnalyticDiscipline/execute?execution_mode={synchronous}",
        json=data_model.model_dump(),
    )
    job = Job(**response.json())
    assert job.job_status == JobStatus.failed.value
    assert job.traceback is not None


@pytest.mark.parametrize(
    "linearization_mode",
    [
        Discipline.LinearizationMode.AUTO,
        Discipline.LinearizationMode.FINITE_DIFFERENCES,
    ],
)
def test_discipline_execution_parametric_discipline_with_gradient(
    tmp_path, test_client, fake_current_active_user, linearization_mode
):
    """Test the discipline execution with the Sellar1 and input data."""
    expressions = {"expressions": {"y_1": "2*x**2", "y_2": "4*x**2+5+z**3"}}
    data = {"x": [1.0], "z": [2.0]}
    post_data = ExecuteInput()
    post_data.input_data = data
    post_data.discipline_options = expressions
    post_data.linearize = True
    post_data.linearization_mode = linearization_mode
    post_data.differentiated_inputs = ["x"]
    post_data.differentiated_outputs = ["y_1"]

    synchronous = ExecutionMode.synchronous.value
    response = test_client.post(
        f"/v1/discipline/AnalyticDiscipline/execute?execution_mode={synchronous}",
        json=post_data.model_dump(),
    )

    discipline = create_discipline("AnalyticDiscipline", **expressions)
    discipline.add_differentiated_inputs(["x"])
    discipline.add_differentiated_outputs(["y_1"])
    discipline.linearization_mode = linearization_mode
    input_data = convert_dict_list_to_array(data)
    jac = discipline.linearize(input_data)

    jac_remote = convert_dict_of_dict_array_to_list(response.json()["jacobian_data"])

    assert jac_remote["y_1"]["x"] == pytest.approx(jac["y_1"]["x"])


def test_discipline_execution_sellar1_async(
    tmp_path, test_client, fake_current_active_user
):
    """Test the discipline execution with the Sellar1 and input data."""
    data = {"x_shared": array([0.0, 1.0]), "y_2": 2.0}
    input_data = convert_dict_array_to_list(data)
    data_model = ExecuteInput()
    data_model.input_data = input_data

    asynchronous = ExecutionMode.asynchronous.value
    response = test_client.post(
        f"/v1/discipline/Sellar1/execute?execution_mode={asynchronous}",
        json=data_model.model_dump(),
    )
    assert response.status_code == 202
    req = test_client.get("/v1/job")
    job = Job(**req.json()[0])
    assert job.job_status == JobStatus.pending


def test_discipline_execution_sellar1_linearization(
    tmp_path, test_client, fake_current_active_user
):
    """Test the discipline execution with the Sellar1 and input data."""
    data = {"x_shared": array([0.0, 1.0]), "y_2": array([1.0])}
    input_data = convert_dict_array_to_list(data)
    data_model = ExecuteInput()
    data_model.input_data = input_data
    data_model.linearize = True
    data_model.linearize_options = {"execute": True, "compute_all_jacobians": True}
    data_model.differentiated_inputs = ["y_2", "x_shared"]
    data_model.differentiated_outputs = ["y_1"]

    synchronous = ExecutionMode.synchronous.value
    response = test_client.post(
        f"/v1/discipline/Sellar1/execute?execution_mode={synchronous}",
        json=data_model.model_dump(),
    )
    out_discipline_remote = convert_dict_list_to_array(response.json()["output_data"])
    jac_remote = convert_dict_of_dict_array_to_list(response.json()["jacobian_data"])

    discipline = create_discipline("Sellar1")
    discipline.add_differentiated_inputs(["y_2", "x_shared"])
    discipline.add_differentiated_outputs(["y_1"])
    out_discipline = discipline.execute(data)

    assert out_discipline_remote["y_1"] == pytest.approx(out_discipline["y_1"])

    jac = discipline.linearize(data)

    assert jac_remote["y_1"]["y_2"] == pytest.approx(jac["y_1"]["y_2"])


def test_get_job_files(tmp_path, test_client, fake_current_active_user):
    """Test the discipline execution endpoint with no input data."""
    synchronous = ExecutionMode.synchronous.value
    response = test_client.post(
        f"/v1/discipline/Sellar1/execute?execution_mode={synchronous}"
    )
    data = response.json()
    job = Job(**data)
    workdir = Path(job.workdir)
    sub_data_dir = workdir / "data" / "sub_data"
    file0 = workdir / "file0.txt"
    file1 = workdir / "data" / "file1.txt"
    file2 = workdir / "data" / "sub_data" / "file2.txt"
    makedirs(sub_data_dir, exist_ok=True)
    for file in [file0, file1, file2]:
        Path(file).write_text("Hello\n")

    response = test_client.get(f"/v1/job/{job.id}/files")
    files = response.json()

    for _line in show_directory_tree(files):
        pass

    flatten_file_paths("data", files)

    flatten_file_paths("data/sub_data", files)

    flatten_file_paths("file0.txt", files)

    flatten_file_paths("data/file1.txt", files)

    flatten_file_paths("data/sub_data/file2.txt", files)

    flatten_file_paths("inexistant_file", files)
