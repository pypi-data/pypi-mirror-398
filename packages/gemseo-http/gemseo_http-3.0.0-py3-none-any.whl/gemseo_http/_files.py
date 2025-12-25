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

"""File structure."""

from __future__ import annotations

import logging
import operator
from collections.abc import Mapping
from functools import reduce
from hashlib import sha256
from pathlib import Path
from pathlib import PurePath
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from collections.abc import Sequence

LOGGER = logging.getLogger(__name__)

# Define a buffer size constant for better readability and maintainability
BUFFER_SIZE = 128 * 1024


def _walk_node(
    node: Mapping[str, Any] | Sequence[str],
    base: Sequence[str] = (),
    paths: Sequence[PurePath] = (),
) -> list[PurePath]:
    """Recursively traverse a nested dictionary and constructs file paths.

    Args:
        node: A hierarchical mapping structure where keys represent
            directory or file names, and values indicate whether they contain nested
            structures (directories) or are files (empty values).
        base: The current base paths during the recursive traversal.
        paths: The resolved file paths.

    Returns:
        The file paths.
    """
    if not paths:
        paths = []
    if not base:
        base = []
    for key, item in node.items():
        file_base = base.copy()
        if isinstance(item, Mapping):
            file_base.append(key)
            _walk_node(item, file_base, paths)
        else:
            file_base.append(key)
            complete_path = PurePath(*file_base)
            paths.append(complete_path)
    return paths


def flatten_file_paths(
    root_path: Path,
    paths_tree: Mapping[str, Any],
) -> list[PurePath]:
    """Return the flatten file paths from a tree of file paths.

    Args:
        root_path: The path to search from.
        paths_tree: A nested mapping representing a directory tree,
            where keys are file/directory names and values indicate
            directory structures (e.g., nested dictionaries).

    Returns:
        The file paths represented as PurePath objects.
        If `root_path` corresponds to a directory, all its files are extracted.
        If it corresponds to a file, only its path is returned. If the name does
        not exist, an empty list is returned.
    """
    dirs = list(PurePath(root_path).parts)
    try:
        obj = reduce(operator.getitem, dirs, paths_tree)
        if obj is None:
            LOGGER.debug("%s is a file.", root_path)
            return [PurePath(root_path)]
        LOGGER.debug(
            "%s is a directory -> Extracting all the files in it...", root_path
        )
        return _walk_node(obj, dirs, [])
    except KeyError:
        LOGGER.warning("%s does not exist remotely. Skipping this file...", root_path)
        return []


def show_directory_tree(dir_path_structure: dict[str, Any], prefix: str = "") -> Any:
    """Recursively generate a visual representation of a directory structure.

    Args:
        dir_path_structure: A dictionary representing a nested directory structure where
            keys are directory or file names and values indicate nested directories or
            empty files.
        prefix: A used for formatting the directory structure view.

    Yields:
        The line of the visual representation of the directory
        structure with prefixes and pointers for clarity.
    """
    space = "    "
    branch = "│   "
    # pointers:
    tee = "├── "
    last = "└── "

    contents = list(dir_path_structure.keys())
    # contents each get pointers that are ├── with a final └── :
    pointers = [tee] * (len(contents) - 1) + [last]
    for pointer, path in zip(pointers, contents, strict=False):
        yield prefix + pointer + path
        if dir_path_structure[path]:  # extend the prefix and recurse:
            extension = branch if pointer == tee else space
            # i.e. space because last, └── , above so no more |
            yield from show_directory_tree(
                dir_path_structure[path], prefix=prefix + extension
            )


def compute_sha256sum(path: Path | str) -> str:
    """Compute the SHA256 checksum of a file.

    Args:
        path: The path of the file.

    Returns:
        The checksum.
    """
    hasher = sha256()
    buffer = bytearray(BUFFER_SIZE)
    memory_buffer = memoryview(buffer)
    with Path(path).open("rb", buffering=0) as file:
        while bytes_read := file.readinto(memory_buffer):
            hasher.update(memory_buffer[:bytes_read])
    return hasher.hexdigest()
