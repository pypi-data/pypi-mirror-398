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

from datetime import datetime
from datetime import timedelta
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from fastapi.exceptions import HTTPException
from jose import JWTError
from jose import jwt

from gemseo_http_server.database import User
from gemseo_http_server.security import authenticate_user
from gemseo_http_server.security import create_token
from gemseo_http_server.security import get_current_active_user
from gemseo_http_server.security import get_current_user
from gemseo_http_server.security import get_user
from gemseo_http_server.settings import Settings

if TYPE_CHECKING:
    from sqlalchemy import Engine


@pytest.fixture
def mock_users():
    return {
        "user1": User(hashed_password="hashed_password1"),
        "user2": User(hashed_password="hashed_password2"),
    }


@pytest.fixture
def mock_verify_password():
    with patch("gemseo_http_server.security.verify_password") as mock_password_checker:
        yield mock_password_checker


def test_authenticate_user_valid_credentials(mock_users, mock_verify_password):
    """Test authenticate_user with valid username and password."""
    mock_verify_password.return_value = True
    user = authenticate_user(mock_users, "user1", "valid_password")
    assert user is not None
    assert isinstance(user, User)


def test_authenticate_user_invalid_username(mock_users, mock_verify_password):
    """Test authenticate_user with an invalid username."""
    mock_verify_password.return_value = False
    user = authenticate_user(mock_users, "nonexistent", "invalid_password")
    assert user is None


def test_authenticate_user_invalid_password(mock_users, mock_verify_password):
    """Test authenticate_user with an invalid password."""
    mock_verify_password.return_value = False
    user = authenticate_user(mock_users, "user1", "invalid_password")
    assert user is None


@pytest.fixture
def mock_load_users_from_db():
    """Fixture for mocking the load_users_from_db function."""
    with patch("gemseo_http_server.security.load_users_from_db") as mock_loader:
        yield mock_loader


@pytest.fixture
def mock_jwt_decode():
    """Fixture for mocking JWT decode."""
    with patch("gemseo_http_server.security.jwt.decode") as mock_decode:
        yield mock_decode


@pytest.mark.anyio
async def test_get_current_user_valid(
    mock_load_users_from_db, mock_jwt_decode, sqldb_fixture
):
    """Test get_current_user with valid token."""

    def fake_engine() -> Engine:
        return sqldb_fixture

    mock_user_data = User(username="valid_user", hashed_password="hashed_password")
    mock_load_users_from_db.return_value = {"valid_user": mock_user_data}
    mock_jwt_decode.return_value = {"sub": "valid_user"}
    token = "valid_token"
    result = await get_current_user(token, fake_engine)
    assert result == mock_user_data


@pytest.mark.anyio
async def test_get_current_token_invalid(mock_jwt_decode, sqldb_fixture):
    """Test get_current_user with invalid token."""

    mock_jwt_decode.side_effect = JWTError
    token = "invalid_token"

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token, None)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Could not validate credentials"


@pytest.mark.anyio
async def test_get_current_user_nonexistent(
    mock_load_users_from_db, mock_jwt_decode, sqldb_fixture
):
    """Test get_current_user with a valid token referencing nonexistent user."""

    def fake_engine() -> Engine:
        return sqldb_fixture

    mock_load_users_from_db.return_value = {}
    mock_jwt_decode.return_value = {"sub": None}
    token = "valid_token"

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token, fake_engine)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Could not validate credentials"


@pytest.fixture
def mock_settings():
    return Settings(secret_key="testsecretkey", algorithm="HS256")


def test_create_access_token_with_expiration(mock_settings):
    """Test creating a token with a specified expiration time."""
    with patch("gemseo_http_server.security.settings", mock_settings):
        data = {"sub": "user@example.com"}
        expires_delta = timedelta(hours=1)
        token = create_token(data, expires_delta)
        decoded_token = jwt.decode(
            token,
            mock_settings.secret_key,
            algorithms=mock_settings.algorithm,
        )
        assert decoded_token["sub"] == data["sub"]
        assert datetime.fromtimestamp(decoded_token["exp"]) > datetime.utcnow()


@pytest.mark.anyio
async def test_get_current_active_user_active():
    """Test retrieving current active user when user is active."""
    current_user = User()
    result = await get_current_active_user(current_user)
    assert result == current_user


@pytest.mark.anyio
async def test_get_current_active_user_inactive():
    """Test retrieving current active user when user is inactive."""
    current_user = User(disabled=True)
    with pytest.raises(HTTPException) as excinfo:
        await get_current_active_user(current_user)
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Inactive user"


def test_create_access_token_default_expiration(mock_settings):
    """Test creating a token with the default expiration time."""
    with patch("gemseo_http_server.security.settings", mock_settings):
        data = {"sub": "user@example.com"}
        token = create_token(data)
        decoded_token = jwt.decode(
            token,
            mock_settings.secret_key,
            algorithms=mock_settings.algorithm,
        )
        assert decoded_token["sub"] == data["sub"]
        assert datetime.fromtimestamp(decoded_token["exp"]) > datetime.utcnow()


def test_create_access_token_invalid_secret_key(mock_settings):
    """Test token decoding with an invalid secret key."""
    with patch("gemseo_http_server.security.settings", mock_settings):
        data = {"sub": "user@example.com"}
        token = create_token(data)
        invalid_secret_key = "invalidsecretkey"
        with pytest.raises(jwt.JWTError):
            jwt.decode(token, invalid_secret_key, algorithms=mock_settings.algorithm)


def test_get_user_with_existing_user():
    """Test getting a user that exists in the database."""
    users_db = {
        "user1": User(hashed_password="hashed_password1"),
        "user2": User(hashed_password="hashed_password2"),
    }
    user = get_user(users_db, "user1")
    assert user is not None
    assert user.hashed_password == "hashed_password1"


def test_get_user_with_nonexistent_user():
    """Test getting a user that does not exist in the database."""
    users_db = {
        "user1": User(hashed_password="hashed_password1"),
        "user2": User(hashed_password="hashed_password2"),
    }
    user = get_user(users_db, "nonexistent_user")
    assert user is None


def test_get_user_with_empty_database():
    """Test getting a user when the database is empty."""
    users_db = {}
    user = get_user(users_db, "user1")
    assert user is None
