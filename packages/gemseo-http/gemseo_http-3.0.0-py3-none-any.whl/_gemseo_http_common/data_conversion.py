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
"""Functions to convert dict and dict of dict of Numpy arrays to list of float.

Ugly and temporary, better serialization methods shall be used in place of list of
floats.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from numpy import array
from numpy import ndarray
from numpy import real
from scipy.sparse import issparse

if TYPE_CHECKING:
    from collections.abc import Mapping

    from gemseo.typing import StrKeyMapping


def convert_dict_list_to_array(data: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a dict of list to a dict of Numpy arrays.

    Args:
        data: The data to convert.

    Returns:
        The converted data.
    """
    data_out = {}
    for key, val in data.items():
        if isinstance(val, list) and (not val or not isinstance(val[0], str)):
            data_out[key] = array(val)
        else:
            data_out[key] = val
    return data_out


def convert_dict_array_to_list(data: StrKeyMapping) -> StrKeyMapping:
    """Convert a dictionary of [str, ndarray] to a dict of [str, list[float]].

    Args:
        data: The data to convert.

    Returns:
        The converted data.
    """
    converted_data = {}
    for key, val in data.items():
        if isinstance(val, ndarray):
            val = val.real
            converted_data[key] = real(val).tolist()
        elif isinstance(val, complex):
            converted_data[key] = real(val)
        else:
            converted_data[key] = val
    return converted_data


def convert_dict_of_dict_array_to_list(
    data: Mapping[str, Mapping[str, ndarray]],
) -> dict[str, dict[str, list[float]]]:
    """Convert a nested dictionary of Numpy array to a dictionary of list of floats.

    Args:
        data: The data to convert.

    Returns:
        The converted data.
    """
    converted_data = {}
    for key, val in data.items():
        converted_data[key] = cd = {}
        for key2, val2 in val.items():
            if isinstance(val2, ndarray):
                cd[key2] = real(val2).tolist()
            elif issparse(val2):
                cd[key2] = real(val2).todense().tolist()
            else:
                cd[key2] = real(val2)
    return converted_data
