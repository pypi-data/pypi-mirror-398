# noqa: INP001
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

"""Sellar disciplines with files."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

from gemseo.core.discipline import Discipline
from numpy import array
from numpy import sqrt

if TYPE_CHECKING:
    from gemseo.typing import StrKeyMapping


class Sellar1XSharedToFile(Discipline):
    """A discipline writing `x_shared` to file."""

    def __init__(self) -> None:  # noqa :D107
        super().__init__()
        input_data = {"x_shared": array([0.0, 0.0])}
        output_data = {"x_shared_file": "input_file.json"}
        self.input_grammar.update_from_data(input_data)
        self.output_grammar.update_from_data(output_data)
        self.default_inputs = input_data

    def _run(self, input_data) -> StrKeyMapping:
        output_filename = "input_file.json"
        input_data_converted = {"x_shared": input_data["x_shared"].tolist()}
        with Path(output_filename).open("w") as json_file:
            json.dump(input_data_converted, json_file)
        return {"x_shared_file": Path(output_filename).resolve().as_posix()}


class Sellar1Y1FileToProcess(Discipline):
    """A discipline reading a file and putting the value into `local_data`."""

    def __init__(self) -> None:  # noqa :D107
        super().__init__()
        input_data = {"y_1_file": "output_file.json"}
        output_data = {"y_1": array([0.0])}
        self.input_grammar.update_from_data(input_data)
        self.output_grammar.update_from_data(output_data)
        self.default_inputs = input_data

    def _run(self, input_data) -> StrKeyMapping:
        with Path(input_data["y_1_file"]).open() as json_file:
            data = json.load(json_file)
        return {"y_1": array(data["y_1"])}


class Sellar1File(Discipline):
    """A Sellar1 Discipline taking as inputs files."""

    def __init__(self, sleep_time: float = 0.0, is_failing: bool = False) -> None:  # noqa :D107
        """
        Args:
            sleep_time: Time to sleep before starting the computation.
            is_failing: Whether to fail the computation.
        """
        super().__init__()
        self._sleep_time = sleep_time
        self._is_failing = is_failing
        input_data = {
            "x_shared_file": "input_file.json",
            "x_1": array([0.0]),
            "y_2": array([0.0]),
        }
        self.input_grammar.update_from_data(input_data)
        output_data = {"y_1_file": "output_file.json"}
        self.output_grammar.update_from_data(output_data)
        # self.default_inputs = input_data
        # self.default_outputs = output_data

    def _run(self, input_data) -> StrKeyMapping:
        if self._is_failing:
            msg = "Sellar1Remote discipline has failed."
            raise RuntimeError(msg)

        time.sleep(self._sleep_time)

        file_content = Path(input_data["x_shared_file"]).read_text()
        json_input_data = json.loads(file_content)
        z = json_input_data["x_shared"]
        x = input_data["x_1"]
        y_2 = input_data["y_2"]

        y_1 = sqrt(z[0] ** 2 + z[1] + x - 0.2 * y_2)

        output_data = {"y_1": y_1}

        out = {}
        for k, v in output_data.items():
            if isinstance(v, (str, float)):
                out[k] = v
            else:
                out[k] = v.tolist()
        output_filename = "output_file.json"
        with Path(output_filename).open("w") as outfile:
            json.dump(out, outfile)
        output_data["y_1_file"] = output_filename

        workdir = Path()
        sub_data_dir = workdir / "data" / "sub_data"
        sub_data_dir_empty = workdir / "data" / "sub_data" / "empty_dir"
        file0 = workdir / "file0.txt"
        file1 = workdir / "data" / "file1.txt"
        file2 = workdir / "data" / "sub_data" / "file2.txt"
        Path(sub_data_dir).mkdir(parents=True)
        Path(sub_data_dir_empty).mkdir(parents=True)
        for file in [file0, file1, file2]:
            Path(file).write_text("Hello\n")

        return output_data


class Sellar1FileMultipleFile(Sellar1File):
    """A Sellar1 Discipline which takes multiple files in the y_1_file."""

    def __init__(self) -> None:  # noqa :D107
        super().__init__()
        self._output_data = {"y_1_file": ["output_file.json", "output_file.json"]}
        self.output_grammar.update_from_data(self._output_data)

    def _run(self, input_data) -> StrKeyMapping:
        _ = super()._run(input_data)
        return self._output_data


class Sellar1FileWrongOutput(Sellar1File):
    """A Sellar1 Discipline with wrong types in output."""

    def __init__(self) -> None:  # noqa :D107
        super().__init__()
        output_data = {"y_1_file": "output_file.json", "y_1": array([0.0])}
        self.output_grammar.update_from_data(output_data)

    def _run(self, input_data) -> StrKeyMapping:
        output_data = dict(super()._run(input_data))
        output_data["y_1"] = array([1.0])
        return output_data
