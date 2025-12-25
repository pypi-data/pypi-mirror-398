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

import unittest
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx
import pytest
from gemseo import create_design_space
from gemseo import create_discipline
from gemseo import create_scenario
from gemseo.algos.opt.nlopt.settings.nlopt_cobyla_settings import NLOPT_COBYLA_Settings
from gemseo.algos.opt.nlopt.settings.nlopt_slsqp_settings import NLOPT_SLSQP_Settings
from gemseo.core.chains.chain import MDOChain
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.mda.jacobi import MDAJacobi
from gemseo.utils.comparisons import compare_dict_of_arrays
from numpy import array
from numpy import ones
from numpy.testing import assert_equal

from _gemseo_http_common.database import Job
from gemseo_http.http_discipline import HTTPDiscipline

from .data.sellar1_files import Sellar1XSharedToFile
from .data.sellar1_files import Sellar1Y1FileToProcess

if TYPE_CHECKING:
    from collections.abc import Callable

DIRPATH = Path(__file__).parent


CLASS_NAME = "Sellar2"


def test_init(test_client):
    """Test the execution of the HTTPDiscipline wrapper."""
    local_disc = create_discipline(CLASS_NAME)

    # With default settings.
    remote_disc = HTTPDiscipline(
        name="RemoteSellar2",
        url="http://localhost",
        user="test",
        password="test",
        class_name=CLASS_NAME,
        http_client=test_client,
    )

    assert remote_disc.input_grammar == local_disc.input_grammar
    assert remote_disc.output_grammar == local_disc.output_grammar

    # Without default settings.
    remote_disc = HTTPDiscipline(
        name="RemoteSellar2",
        class_name=CLASS_NAME,
        user="test",
        password="test",
        url="http://testserver",
        port=50000,
        http_client=test_client,
    )
    assert remote_disc.input_grammar == local_disc.input_grammar
    assert remote_disc.output_grammar == local_disc.output_grammar
    for key in local_disc.default_input_data:
        assert_equal(
            remote_disc.default_input_data[key], local_disc.default_input_data[key]
        )


@pytest.fixture
def mock_get_default_input_data(test_client):
    original_post = test_client.post

    def new_post(*args, **kwargs):
        """Mock only the post method to get the default input data."""
        url = args[0]
        if "default_input_data" in url:
            return httpx.Response(
                status_code=401, content="Incorrect username or password."
            )
        return original_post(args[0], **kwargs)

    test_client.post = new_post
    yield test_client
    test_client.post = original_post


def test_init_failed_get_default_input(mock_get_default_input_data):
    """Test the execution of the HTTPDiscipline wrapper."""
    with pytest.raises(
        ConnectionError, match=r"Error while fetching the default input data."
    ):
        HTTPDiscipline(
            name="RemoteSellar2",
            url="http://localhost",
            user="test",
            password="test",
            class_name=CLASS_NAME,
            http_client=mock_get_default_input_data,
        )


@pytest.fixture
def mock_get_token(test_client):
    original_post = test_client.post

    def new_post(*args, **kwargs):
        """Mock only the post method to get the default input data."""
        url = args[0]
        if "token" in url:
            return httpx.Response(
                status_code=401, content="Incorrect username or password."
            )
        return original_post(args[0], **kwargs)

    test_client.post = new_post
    yield test_client
    test_client.post = original_post


def test_init_failed_get_token(mock_get_token):
    """Test the execution of the HTTPDiscipline wrapper."""
    with pytest.raises(
        ConnectionError, match=r"Cannot obtain a token with the current login/password."
    ):
        HTTPDiscipline(
            name="RemoteSellar2",
            url="http://localhost",
            user="test",
            password="test",
            class_name=CLASS_NAME,
            http_client=mock_get_token,
        )


def test_http_discipline_unknown_discipline(test_client):
    """Test the execution of the HTTPDiscipline wrapper."""
    match = (
        r"Request .* failed with error code 404. The remote error is:"
        r" The class UnknownDiscipline is not available;"
        r" the available ones are: .* "
    )
    with pytest.raises(RuntimeError, match=match):
        HTTPDiscipline(
            name="RemoteSellar2",
            class_name="UnknownDiscipline",
            url="http://localhost",
            user="test",
            password="test",
            http_client=test_client,
        )


def test_http_discipline_execute_wo_file_sync(test_client):
    """Test the execution of the HTTPDiscipline wrapper."""
    local_disc = create_discipline(CLASS_NAME)
    remote_disc = HTTPDiscipline(
        name="RemoteSellar2",
        url="http://localhost",
        user="test",
        password="test",
        class_name=CLASS_NAME,
        http_client=test_client,
    )

    data = {"x_shared": array([0.0, 1.0]), "y_1": array([0.0]), "x_2": array([1.0])}
    assert compare_dict_of_arrays(remote_disc.execute(data), local_disc.execute(data))

    for compute_all_jacobians, execute in zip(
        (True, False), (True, False), strict=False
    ):
        # Prevent using the cache.
        data["x_shared"] += 1.0

        local_disc.linearize(
            data, compute_all_jacobians=compute_all_jacobians, execute=execute
        )
        remote_disc.linearize(
            data, compute_all_jacobians=compute_all_jacobians, execute=execute
        )

        assert compare_dict_of_arrays(remote_disc.jac, local_disc.jac)


def test_http_discipline_execute_wo_file_sync_options(test_client):
    """Test the execution of the HTTPDiscipline wrapper."""
    expressions = {"expressions": {"y_1": "2*x**2", "y_2": "4*x**2+5+z**3"}}
    local_disc = create_discipline("AnalyticDiscipline", **expressions)
    remote_disc = HTTPDiscipline(
        name="RemoteAnalytic",
        class_name="AnalyticDiscipline",
        url="http://localhost",
        user="test",
        password="test",
        discipline_options=expressions,
        http_client=test_client,
    )

    data = {"x": array([1.0]), "z": array([2.0])}
    assert compare_dict_of_arrays(remote_disc.execute(data), local_disc.execute(data))

    for compute_all_jacobians, execute in zip(
        (True, False), (True, False), strict=False
    ):
        # Prevent using the cache.
        data["x"] += 1.0

        local_disc.linearize(
            data, compute_all_jacobians=compute_all_jacobians, execute=execute
        )
        remote_disc.linearize(
            data, compute_all_jacobians=compute_all_jacobians, execute=execute
        )

        assert compare_dict_of_arrays(remote_disc.jac, local_disc.jac)


def test_http_discipline_execute_timeout(tmp_wd, test_client, create_fake_poll_job):
    """Test the execution of the HTTPDiscipline wrapper."""
    remote_disc = HTTPDiscipline(
        name="RemoteSellar1",
        class_name="Sellar1",
        url="http://localhost",
        user="test",
        password="test",
        is_asynchronous=True,
        http_client=test_client,
        execution_timeout=1,
    )
    data = {
        "x_shared": array([1.0, 2.0]),
        "x_1": array([0.0]),
        "y_2": array([0.0]),
    }

    with (
        pytest.raises(RuntimeError, match=r"Execution time exceeded 1s."),
        unittest.mock.patch.object(
            remote_disc, "_HTTPDiscipline__poll_job", create_fake_poll_job
        ),
    ):
        remote_disc.execute(data)


def test_http_discipline_execute_no_long_polling(tmp_wd, test_client, sqldb_fixture):
    """Test the HTTPDiscipline in async mode and without long polling."""

    def fake_engine():
        return sqldb_fixture

    with patch("gemseo_http_server.gemseo_runner.create_engine", fake_engine):
        remote_disc = HTTPDiscipline(
            name="RemoteSellar1",
            class_name="Sellar1",
            url="http://localhost",
            user="test",
            password="test",
            is_asynchronous=True,
            use_long_polling=False,
            polling_wait_time=0,
            http_client=test_client,
        )

        class FakePollJob:
            """A Callable class for testing purposes.

            This class enables to test a polling loop.
            As the code-under-test is aimed to be run in async mode,
            the following class mimics a first iteration that produce a pending job.
            The next iterations are done by the real __poll_job method.
            """

            def __init__(self, initial_poll_job: Callable):
                self._calls_to_poll_job = 0
                self._initial_poll_job = initial_poll_job

            def __call__(self, job_id):
                """Fake poll job method for testing purposes.

                Args:
                    job_id: The job id.

                Returns:
                    A fake pending Jobs object.
                """
                self._calls_to_poll_job += 1
                if self._calls_to_poll_job > 1:
                    return self._initial_poll_job(job_id)
                return Job(id=job_id, user_id=1, job_status="pending")

        fake_poll_job = FakePollJob(remote_disc._HTTPDiscipline__poll_job)
        with unittest.mock.patch.object(
            remote_disc, "_HTTPDiscipline__poll_job", fake_poll_job
        ):
            data = {
                "x_shared": array([1.0, 2.0]),
                "x_1": array([0.0]),
                "y_2": array([0.0]),
            }
            out = remote_disc.execute(data)
            assert out["y_1"] == pytest.approx(1.7320508075688772)


def test_http_discipline_execute_w_file_sync(tmp_wd, test_client):
    """Test the execution of the HTTPDiscipline wrapper."""
    remote_disc = HTTPDiscipline(
        name="RemoteSellar1WithFile",
        class_name="Sellar1File",
        url="http://localhost",
        user="test",
        password="test",
        inputs_to_upload=["x_shared_file"],
        outputs_to_download=["y_1_file"],
        file_paths_to_upload=[DIRPATH / "data" / "test.pdf"],
        file_paths_to_download=["test.pdf", "data//sub_data//", "nonexistingfolder"],
        http_client=test_client,
    )

    discipline_xshared_to_file = Sellar1XSharedToFile()
    y1_file_to_data = Sellar1Y1FileToProcess()
    chain = MDOChain([discipline_xshared_to_file, remote_disc, y1_file_to_data])
    data = {"x_shared": array([1.0, 2.0]), "x_1": array([0.0]), "y_2": array([0.0])}
    out = chain.execute(data)
    assert out["y_1"] == pytest.approx(1.7320508075688772)


def test_http_discipline_execute_w_file_sync_multiple_files(tmp_wd, test_client):
    """Test the execution of the HTTPDiscipline wrapper."""
    remote_disc = HTTPDiscipline(
        name="RemoteSellar1WithFile",
        class_name="Sellar1FileMultipleFile",
        url="http://localhost",
        user="test",
        password="test",
        inputs_to_upload=["x_shared_file"],
        outputs_to_download=["y_1_file"],
        file_paths_to_upload=[DIRPATH / "data" / "test.pdf"],
        file_paths_to_download=["test.pdf", "data//sub_data//", "nonexistingfolder"],
        http_client=test_client,
    )
    discipline_xshared_to_file = Sellar1XSharedToFile()
    chain = MDOChain([discipline_xshared_to_file, remote_disc])
    data = {"x_shared": array([1.0, 2.0]), "x_1": array([0.0]), "y_2": array([0.0])}
    chain.execute(data)


def test_http_discipline_execute_w_file_sync_output_no_file(tmp_wd, test_client):
    """Test the execution of the HTTPDiscipline wrapper."""
    remote_disc = HTTPDiscipline(
        name="RemoteSellar1WithFile",
        class_name="Sellar1FileWrongOutput",
        url="http://localhost",
        user="test",
        password="test",
        inputs_to_upload=["x_shared_file"],
        outputs_to_download=["y_1"],
        file_paths_to_upload=[DIRPATH / "data" / "test.pdf"],
        file_paths_to_download=["test.pdf", "data//sub_data//", "nonexistingfolder"],
        http_client=test_client,
    )
    discipline_xshared_to_file = Sellar1XSharedToFile()
    chain = MDOChain([discipline_xshared_to_file, remote_disc])
    data = {"x_shared": array([1.0, 2.0]), "x_1": array([0.0]), "y_2": array([0.0])}
    with pytest.raises(TypeError, match="Wrong type for the variable holding a file:"):
        chain.execute(data)


def test_http_discipline_execute_w_file_sync_wrong_hash(tmp_wd, test_client):
    """Check that an error is raised when the hash of
    the file to upload does not match."""
    remote_disc = HTTPDiscipline(
        name="RemoteSellar1WithFile",
        class_name="Sellar1File",
        url="http://localhost",
        user="test",
        password="test",
        inputs_to_upload=["x_shared_file"],
        outputs_to_download=["y_1_file"],
        file_paths_to_upload=[DIRPATH / "data" / "test.pdf"],
        file_paths_to_download=["test.pdf", "data//sub_data//", "nonexistingfolder"],
        http_client=test_client,
    )

    discipline_xshared_to_file = Sellar1XSharedToFile()
    y1_file_to_data = Sellar1Y1FileToProcess()
    chain = MDOChain([discipline_xshared_to_file, remote_disc, y1_file_to_data])
    data = {"x_shared": array([1.0, 2.0]), "x_1": array([0.0]), "y_2": array([0.0])}
    with (
        unittest.mock.patch(
            "gemseo_http.http_discipline.HTTPDiscipline._HTTPDiscipline__get_file_hashes",
            return_value=("global_hash", ["hash1, hash2"]),
        ),
        pytest.raises(ValueError, match="File hash mismatch"),
    ):
        chain.execute(data)


@pytest.mark.parametrize("use_long_polling", [True, False])
@pytest.mark.parametrize("polling_wait_time", [1, 2])
@pytest.mark.parametrize("sleep_time", [0.0, 3.0])
def test_http_discipline_execute_w_file_async(
    tmp_wd,
    sqldb_fixture,
    test_client,
    use_long_polling,
    polling_wait_time,
    sleep_time,
):
    """Test the execution of the HTTPDiscipline wrapper."""

    def fake_engine():
        return sqldb_fixture

    with patch("gemseo_http_server.gemseo_runner.create_engine", fake_engine):
        remote_disc = HTTPDiscipline(
            name="RemoteSellar1WithFile",
            class_name="Sellar1File",
            url="http://localhost",
            user="test",
            password="test",
            is_asynchronous=True,
            inputs_to_upload=["x_shared_file"],
            outputs_to_download=["y_1_file"],
            use_long_polling=use_long_polling,
            polling_wait_time=polling_wait_time,
            discipline_options={
                "sleep_time": sleep_time,
            },
            http_client=test_client,
        )

        # Write data to disk
        discipline_xshared_to_file = Sellar1XSharedToFile()

        # Transfer disk data to process
        y1_file_to_data = Sellar1Y1FileToProcess()

        chain = MDOChain([discipline_xshared_to_file, remote_disc, y1_file_to_data])

        data = {"x_shared": array([1.0, 2.0]), "x_1": array([0.0]), "y_2": array([0.0])}
        out = chain.execute(data)
        assert out["y_1"] == pytest.approx(1.73205081)


@pytest.mark.parametrize("is_asynchronous", [True, False])
def test_http_discipline_execute_failing(
    tmp_wd, sqldb_fixture, test_client, is_asynchronous
):
    """Test the execution of the HTTPDiscipline wrapper."""

    def fake_engine():
        return sqldb_fixture

    with patch("gemseo_http_server.gemseo_runner.create_engine", fake_engine):
        remote_disc = HTTPDiscipline(
            name="RemoteSellar1WithFile",
            class_name="Sellar1File",
            url="http://localhost",
            user="test",
            password="test",
            is_asynchronous=is_asynchronous,
            inputs_to_upload=["x_shared_file"],
            outputs_to_download=["y_1_file"],
            discipline_options={
                "is_failing": True,
            },
            http_client=test_client,
        )

        # Write data to disk
        discipline_xshared_to_file = Sellar1XSharedToFile()

        # Transfer disk data to process
        y1_file_to_data = Sellar1Y1FileToProcess()

        chain = MDOChain([discipline_xshared_to_file, remote_disc, y1_file_to_data])

        data = {"x_shared": array([1.0, 2.0]), "x_1": array([0.0]), "y_2": array([0.0])}
        with pytest.raises(RuntimeError, match=r"Sellar1Remote discipline has failed."):
            chain.execute(data)


def test_http_discipline_execute_failing_while_uploading_file(
    tmp_wd, sqldb_fixture, test_client
):
    """Test the execution of the HTTPDiscipline wrapper."""

    def fake_engine():
        return sqldb_fixture

    with patch("gemseo_http_server.gemseo_runner.create_engine", fake_engine):
        remote_disc = HTTPDiscipline(
            name="RemoteSellar1WithFile",
            class_name="Sellar1File",
            url="http://localhost",
            user="test",
            password="test",
            inputs_to_upload=["x_shared_file"],
            is_asynchronous=True,
            discipline_options={
                "is_failing": False,
            },
            http_client=test_client,
        )

        data = {
            "x_shared_file": str(DIRPATH / "data" / "input_file.json"),
            "x_1": array([0.0]),
            "y_2": array([0.0]),
        }

        def fake_post(url, json=None, files=None, data=None):
            return httpx.Response(
                status_code=500, text="Something went wrong while calling the server"
            )

        with (
            pytest.raises(RuntimeError, match="Failed to upload the file"),
            unittest.mock.patch.object(remote_disc._http_client, "post", fake_post),
        ):
            remote_disc.execute(data)


def test_http_discipline_execute_failing_while_posting(
    tmp_wd, sqldb_fixture, test_client
):
    """Test the execution of the HTTPDiscipline wrapper."""

    def fake_engine():
        return sqldb_fixture

    with patch("gemseo_http_server.gemseo_runner.create_engine", fake_engine):
        remote_disc = HTTPDiscipline(
            name="RemoteSellar1WithFile",
            class_name="Sellar1File",
            url="http://localhost",
            user="test",
            password="test",
            is_asynchronous=True,
            discipline_options={
                "is_failing": False,
            },
            http_client=test_client,
        )
        # Write data to disk

        data = {
            "x_shared_file": "dummy_string",
            "x_1": array([0.0]),
            "y_2": array([0.0]),
        }

        def fake_post(url, json=None, files=None, data=None):
            return httpx.Response(
                status_code=500, text="Something went wrong while calling the server"
            )

        with (
            pytest.raises(
                RuntimeError, match="Something went wrong while calling the server"
            ),
            unittest.mock.patch.object(remote_disc._http_client, "post", fake_post),
        ):
            remote_disc.execute(data)


def test_sellar_mdo_http_discipline_sync_wo_file(test_client):
    """Test the execution of a MDO Scenario with an HTTP discipline.

    This test is without file transfer.
    """
    sellar1, sellar_system = create_discipline(["Sellar1", "SellarSystem"])
    sellar2 = HTTPDiscipline(
        name="RemoteSellar2",
        class_name=CLASS_NAME,
        http_client=test_client,
        user="test",
        password="test",
        url="http://localhost",
    )
    disciplines = [sellar1, sellar2, sellar_system]
    design_space = create_design_space()
    design_space.add_variable("x_1", lower_bound=0.0, upper_bound=10.0, value=ones(1))
    design_space.add_variable(
        "x_shared",
        2,
        lower_bound=array([-10, 0.0]),
        upper_bound=array([10.0, 10.0]),
        value=array([4.0, 3.0]),
    )
    design_space.add_variable(
        "y_1", lower_bound=-100.0, upper_bound=100.0, value=ones(1)
    )
    design_space.add_variable(
        "y_2", lower_bound=-100.0, upper_bound=100.0, value=ones(1)
    )

    scenario = create_scenario(
        disciplines,
        formulation_name="MDF",
        objective_name="obj",
        design_space=design_space,
    )
    scenario.add_constraint("c_1", MDOFunction.ConstraintType.INEQ)
    scenario.add_constraint("c_2", MDOFunction.ConstraintType.INEQ)
    settings = NLOPT_COBYLA_Settings(max_iter=1000)
    scenario.execute(settings)
    assert scenario.optimization_result.f_opt == pytest.approx(3.18337, abs=1e-3)


def test_sellar_mda_linearize(test_client):
    """Test an MDA with linearization with HTTPDiscipline."""
    sellar1, sellar2, sellar_system = create_discipline([
        "Sellar1",
        CLASS_NAME,
        "SellarSystem",
    ])
    sellar2_http = HTTPDiscipline(
        name="RemoteSellar2",
        class_name=CLASS_NAME,
        url="http://localhost",
        user="test",
        password="test",
        http_client=test_client,
    )
    disciplines_ref = [sellar1, sellar2, sellar_system]
    disciplines = [sellar1, sellar2_http, sellar_system]

    data = {"x_1": array([1.0]), "x_shared": array([4.0, 3.0])}
    mda_jacobi = MDAJacobi(disciplines=disciplines)
    mda_jacobi_ref = MDAJacobi(disciplines=disciplines_ref)
    out = mda_jacobi.execute(data)
    out_2 = mda_jacobi_ref.execute(data)

    assert out["obj"] == pytest.approx(out_2["obj"])


def test_sellar_mdo_http_discipline_sync_wo_file_linearize(test_client):
    """Test the execution of a MDO Scenario with an HTTP discipline.

    This test is without file transfer.
    """
    sellar1, sellar_system = create_discipline(["Sellar1", "SellarSystem"])
    sellar2 = HTTPDiscipline(
        name="RemoteSellar2",
        class_name=CLASS_NAME,
        url="http://localhost",
        user="test",
        password="test",
        http_client=test_client,
    )

    disciplines = [sellar1, sellar2, sellar_system]

    design_space = create_design_space()
    design_space.add_variable("x_1", lower_bound=0.0, upper_bound=10.0, value=ones(1))
    design_space.add_variable(
        "x_shared",
        2,
        lower_bound=array([-10, 0.0]),
        upper_bound=array([10.0, 10.0]),
        value=array([4.0, 3.0]),
    )
    design_space.add_variable(
        "y_1", lower_bound=-100.0, upper_bound=100.0, value=ones(1)
    )
    design_space.add_variable(
        "y_2", lower_bound=-100.0, upper_bound=100.0, value=ones(1)
    )

    scenario = create_scenario(
        disciplines,
        formulation_name="MDF",
        objective_name="obj",
        design_space=design_space,
    )
    scenario.add_constraint("c_1", MDOFunction.ConstraintType.INEQ)
    scenario.add_constraint("c_2", MDOFunction.ConstraintType.INEQ)
    settings = NLOPT_SLSQP_Settings(max_iter=100)
    scenario.execute(settings)
    assert scenario.optimization_result.f_opt == pytest.approx(3.18339395, abs=1e-3)


def test_file_transfer_in_chain(tmp_wd, test_client):
    sellar1_ref = create_discipline("Sellar1")

    discipline_sellar1 = HTTPDiscipline(
        name="RemoteSellar1WithFile",
        class_name="Sellar1File",
        url="http://localhost",
        user="test",
        password="test",
        inputs_to_upload=["x_shared_file"],
        outputs_to_download=["y_1_file"],
        http_client=test_client,
    )

    # Write data to disk
    discipline_xshared_to_file = Sellar1XSharedToFile()

    # Transfer disk data to process
    y1_file_to_data = Sellar1Y1FileToProcess()
    y1_file_to_data.cache = None

    sellar1 = MDOChain([
        discipline_xshared_to_file,
        discipline_sellar1,
        y1_file_to_data,
    ])

    data1 = {"x_shared": array([0.0, 1.0]), "y_2": array([0.0]), "x_1": array([1.0])}
    data2 = {"x_shared": array([1.0, 2.0]), "y_2": array([1.0]), "x_1": array([2.0])}
    data3 = {"x_shared": array([2.0, 3.0]), "y_2": array([2.0]), "x_1": array([3.0])}
    data4 = {"x_shared": array([3.0, 4.0]), "y_2": array([3.0]), "x_1": array([4.0])}
    data5 = {"x_shared": array([4.0, 5.0]), "y_2": array([4.0]), "x_1": array([5.0])}

    for data in [data1, data2, data3, data4, data5]:
        res = sellar1.execute(data)
        res_ref = sellar1_ref.execute(data)
        assert res["y_1"] == res_ref["y_1"]


def test_sellar_mdo_http_discipline_sync_with_file(tmp_wd, test_client):
    """Test the execution of the HTTPDiscipline wrapper.

    Currently, a server needs to be executed beforehand. request shall be mocked in
    order to test the wrapper in isolation. The Webapp is tested separately, and it is
    not necessary to have a live Webapp.
    """
    sellar2, sellar_system = create_discipline([CLASS_NAME, "SellarSystem"])

    discipline_sellar1 = HTTPDiscipline(
        name="RemoteSellar1WithFile",
        class_name="Sellar1File",
        url="http://localhost",
        user="test",
        password="test",
        inputs_to_upload=["x_shared_file"],
        outputs_to_download=["y_1_file"],
        http_client=test_client,
    )

    # Write data to disk
    discipline_xshared_to_file = Sellar1XSharedToFile()

    # Transfer disk data to process
    y1_file_to_data = Sellar1Y1FileToProcess()
    y1_file_to_data.cache = None

    sellar1 = MDOChain([
        discipline_xshared_to_file,
        discipline_sellar1,
        y1_file_to_data,
    ])
    disciplines = [sellar1, sellar2, sellar_system]
    design_space = create_design_space()
    design_space.add_variable("x_1", lower_bound=0.0, upper_bound=10.0, value=ones(1))
    design_space.add_variable(
        "x_shared",
        2,
        lower_bound=array([-10, 0.0]),
        upper_bound=array([10.0, 10.0]),
        value=array([4.0, 3.0]),
    )
    design_space.add_variable(
        "y_1", lower_bound=-100.0, upper_bound=100.0, value=ones(1)
    )
    design_space.add_variable(
        "y_2", lower_bound=-100.0, upper_bound=100.0, value=ones(1)
    )

    scenario = create_scenario(
        disciplines,
        formulation_name="MDF",
        objective_name="obj",
        design_space=design_space,
    )
    scenario.add_constraint("c_1", MDOFunction.ConstraintType.INEQ)
    scenario.add_constraint("c_2", MDOFunction.ConstraintType.INEQ)
    settings = NLOPT_COBYLA_Settings(max_iter=1000)
    scenario.execute(settings)
    assert scenario.optimization_result.f_opt == pytest.approx(3.18337, abs=1e-3)
