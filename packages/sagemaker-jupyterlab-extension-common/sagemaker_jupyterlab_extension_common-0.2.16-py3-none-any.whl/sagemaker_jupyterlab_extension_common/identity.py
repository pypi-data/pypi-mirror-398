"""SageMaker Studio Identity Provider Class

This extends jupyter_server IdentityProvider interface
to provide SageMaker Studio user profile name as user name in Real Time Collaboration mode

"""

import base64
import jwt  # PyJWT
from jwt import InvalidTokenError

from jupyter_server.auth.identity import IdentityProvider, User
from jupyter_server.base.handlers import JupyterHandler


class SagemakerIdentityProvider(IdentityProvider):
    def get_user(self, handler: JupyterHandler) -> User:
        """Get User Info
        Get SageMaker Studio user profile from cookie "studioUserProfileName" and return as a User type

        """
        studio_user_profile_name = handler.get_cookie("studioUserProfileName")

        if not studio_user_profile_name:
            studio_user_profile_name = "User"

        user_id = name = display_name = studio_user_profile_name
        initials = studio_user_profile_name[0].upper()
        color = None
        return User(user_id, name, display_name, initials, None, color)


class WorkSpaceIdentityProvider(IdentityProvider):
    """
    This extends jupyter_server IdentityProvider interface
    to provide workspace user name as user name used in Real Time Collaboration use case.
    """

    COOKIE_NAME = "workspace_auth"
    DEFAULT_USER = "workspace-user"

    def get_user(self, handler: JupyterHandler) -> User:
        """Return a User object decoded from workspace_auth JWT token cookie"""
        cookie_value = handler.get_cookie(self.COOKIE_NAME)

        if not cookie_value:
            return self._make_user(self.DEFAULT_USER)

        # Step 1: JWT tokens may be base64-encoded in the cookie
        try:
            token_str = base64.b64decode(cookie_value).decode("utf-8")
        except Exception:
            token_str = cookie_value  # fallback if cookie already plain JWT

        # Step 2: Decode JWT (without verifying signature unless specified)
        try:
            payload = jwt.decode(token_str, options={"verify_signature": False})
        except InvalidTokenError:
            payload = {}

        # Step 3: Extract user identity
        workspace_user = payload.get("User") or self.DEFAULT_USER
        return self._make_user(workspace_user)

    def _make_user(self, username: str) -> User:
        user_id = name = display_name = username
        initials = username[0].upper()
        return User(user_id, name, display_name, initials, avatar_url=None, color=None)
