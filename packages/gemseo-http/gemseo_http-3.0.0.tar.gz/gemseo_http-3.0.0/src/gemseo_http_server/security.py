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

"""Security functions to secure the webapp."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import TYPE_CHECKING
from typing import Annotated

from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from jose import jwt
from pwdlib import PasswordHash
from starlette import status

from gemseo_http_server.database import User  # noqa: TC001
from gemseo_http_server.database import create_engine
from gemseo_http_server.models import TokenData
from gemseo_http_server.settings import Settings
from gemseo_http_server.utils import load_users_from_db

if TYPE_CHECKING:
    from sqlalchemy import Engine


password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


settings = Settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify the password against the stored hashed one.

    Args:
        plain_password: The plain password.
        hashed_password: The hashed password.

    Returns:
        Whether the two passwords match.
    """
    return password_hash.verify(plain_password, hashed_password)


def get_user(db: dict[str, User], username: str) -> User | None:
    """Return the user in the user database, if it exists.

    Args:
        db: The user database.
        username: The queried username.

    Returns:
        The user entry in a database.
    """
    if username in db:
        return db[username]
    return None


def authenticate_user(
    users: dict[str, User],
    username: str,
    password: str,
) -> User | None:
    """Authenticate the user.

    Args:
        users: The user.
        username: The provided username.
        password: The provided password.

    Returns:
        If username and password are in db, then returns the user.
        Otherwise, return None.
    """
    user = get_user(users, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_token(
    data: dict[str, str],
    expires_delta: timedelta | None = None,
) -> str:
    """Create the access JSON Web Token (JWT).

    Args:
        data: The data to encode in the JSON Web token.
        expires_delta: The time duration (in seconds) of the token.

    Returns:
        The JSON Web Token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user(  # noqa: RUF029
    token: Annotated[str, Depends(oauth2_scheme)],
    engine: Engine = Depends(create_engine),  # noqa: B008
) -> User:
    """Return the current user from the token, if valid.

    Args:
        token: The issued token.
        engine: The database engine.

    Returns:
        The user.

    Raises:
        HTTPException: If the JSON Web Token is not valid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception from JWTError
    users = load_users_from_db(engine)
    user = get_user(users, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(  # noqa: RUF029
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Return the current active user.

    Args:
        current_user: The current user.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
