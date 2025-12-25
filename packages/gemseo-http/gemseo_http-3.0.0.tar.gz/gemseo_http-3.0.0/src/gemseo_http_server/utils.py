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

"""Utils."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from sqlmodel import Session
from sqlmodel import select

from gemseo_http_server.database import User

if TYPE_CHECKING:
    from sqlalchemy import Engine


def load_users_from_db(engine: Engine) -> dict[str, User]:
    """Load the user database.

    Args:
        engine: The database engine.

    Returns:
        The user database.
    """
    with Session(engine) as session:
        statement = select(User)
        results = session.exec(statement).all()
        users_db = {}
        for result in results:
            users_db[result.username] = result
        return users_db


def compute_sha256sum(path: Path | str) -> str:
    """Compute a SHA256 sum of a file.

    Args:
        path: The file path.

    Returns:
        The SHA256 sum of control.
    """
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with Path(path).open("rb", buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()
