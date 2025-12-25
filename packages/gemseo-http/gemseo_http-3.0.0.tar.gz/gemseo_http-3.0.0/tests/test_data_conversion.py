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

"""Tests for the data_conversion module."""

from __future__ import annotations

import numpy as np

from _gemseo_http_common.data_conversion import convert_dict_array_to_list
from _gemseo_http_common.data_conversion import convert_dict_list_to_array


def test_convert_dict_list_to_np():
    """Test the conversion from dict of lists to dict of NumPy arrays."""
    # Given
    data = {
        "x": [1.0, 2.0, 3.0],
        "y": [4.0, 5.0, 6.0],
        "name": "test",
        "strings": ["a", "b", "c"],
    }

    # When
    result = convert_dict_list_to_array(data)

    # Then
    assert isinstance(result["x"], np.ndarray)
    assert isinstance(result["y"], np.ndarray)
    assert isinstance(result["name"], str)
    assert isinstance(result["strings"], list)
    assert np.array_equal(result["x"], np.array([1.0, 2.0, 3.0]))
    assert np.array_equal(result["y"], np.array([4.0, 5.0, 6.0]))
    assert result["name"] == "test"
    assert result["strings"] == ["a", "b", "c"]


def test_convert_dict_np_to_list():
    """Test the conversion from dict of NumPy arrays to dict of lists."""
    # Given
    data = {
        "x": np.array([1.0, 2.0, 3.0]),
        "y": np.array([4.0, 5.0, 6.0]),
        "name": "test",
    }

    # When
    result = convert_dict_array_to_list(data)

    # Then
    assert isinstance(result["x"], list)
    assert isinstance(result["y"], list)
    assert isinstance(result["name"], str)
    assert result["x"] == [1.0, 2.0, 3.0]
    assert result["y"] == [4.0, 5.0, 6.0]
    assert result["name"] == "test"


def test_convert_dict_np_to_list_with_complex():
    """Test the conversion from dict of complex NumPy arrays to dict of lists."""
    # Given
    data = {
        "x": np.array([1.0 + 2j, 2.0 + 3j, 3.0 + 4j]),
        "y": 4.0 + 5j,
    }

    # When
    result = convert_dict_array_to_list(data)

    # Then
    assert isinstance(result["x"], list)
    assert result["x"] == [1.0, 2.0, 3.0]
    assert result["y"] == 4.0
