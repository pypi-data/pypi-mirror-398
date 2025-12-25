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

from numpy import array

if TYPE_CHECKING:
    from numpy import ndarray


def convert_dict_of_dict_list_to_array(
    data: dict[str, dict[str, list[float]]],
) -> dict[str, dict[str, ndarray]]:
    """Convert a nested dict of list to a nested dict of Numpy array.

    Args:
        data: The data to convert.

    Returns:
        The converted data.
    """
    converted_data = {}
    for key, val in data.items():
        converted_data[key] = cd = {}
        for key2, val2 in val.items():
            if isinstance(val2, list):
                cd[key2] = array(val2)
            else:
                cd[key2] = val2
    return converted_data
