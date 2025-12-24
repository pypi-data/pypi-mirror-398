from jupyter_server.auth.identity import User
from ..identity import SagemakerIdentityProvider, WorkSpaceIdentityProvider
import pytest
import base64
import jwt
from unittest.mock import MagicMock


@pytest.fixture
def handler_mock():
    return MagicMock()


def test_get_user_with_cookie(handler_mock):
    handler_mock.get_cookie.return_value = "UserName"
    sm_provider = SagemakerIdentityProvider()
    user = sm_provider.get_user(handler_mock)
    expected_user = User("UserName", "UserName", "UserName", "U", None, None)
    assert user == expected_user


def test_get_user_without_cookie(handler_mock):
    handler_mock.get_cookie.return_value = None
    sm_provider = SagemakerIdentityProvider()
    user = sm_provider.get_user(handler_mock)
    expected_user = User("User", "User", "User", "U", None, None)
    assert user == expected_user


@pytest.fixture
def provider():
    """Fixture for WorkSpaceIdentityProvider instance."""
    return WorkSpaceIdentityProvider()


def make_jwt(payload: dict, secret: str = "dummy-secret") -> str:
    """Helper to make a signed JWT token for testing."""
    return jwt.encode(payload, key=secret, algorithm="HS256")


def test_get_user_no_cookie(provider, handler_mock):
    """Should return default user when cookie missing."""
    handler_mock.get_cookie.return_value = None

    user = provider.get_user(handler_mock)
    assert user.name == WorkSpaceIdentityProvider.DEFAULT_USER
    assert user.initials == "W"


def test_get_user_plain_jwt_cookie(provider, handler_mock):
    """Should decode plain JWT cookie and extract User field."""
    token = make_jwt({"User": "alice"})
    handler_mock.get_cookie.return_value = token

    user = provider.get_user(handler_mock)
    assert user.name == "alice"
    assert user.display_name == "alice"
    assert user.initials == "A"


def test_get_user_base64_jwt_cookie(provider, handler_mock):
    """Should handle base64 encoded JWT cookie."""
    token = make_jwt({"User": "bob"})
    encoded = base64.b64encode(token.encode("utf-8")).decode("utf-8")
    handler_mock.get_cookie.return_value = encoded

    user = provider.get_user(handler_mock)
    assert user.name == "bob"
    assert user.initials == "B"


def test_get_user_invalid_jwt(provider, handler_mock):
    """Should fallback to default user when JWT is invalid."""
    handler_mock.get_cookie.return_value = "not_a_valid_jwt"

    user = provider.get_user(handler_mock)
    assert user.name == WorkSpaceIdentityProvider.DEFAULT_USER
    assert user.initials == "W"


def test_get_user_base64_invalid(provider, handler_mock):
    """Should fallback gracefully if base64 decoding fails."""
    handler_mock.get_cookie.return_value = "###not-base64###"

    user = provider.get_user(handler_mock)
    assert user.name == WorkSpaceIdentityProvider.DEFAULT_USER
    assert user.initials == "W"
