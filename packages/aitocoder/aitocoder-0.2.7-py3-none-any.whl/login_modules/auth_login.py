"""auth.py

This module handles core authentication logic:
check, login, save.
"""
import time
from typing import Optional
from .api_client import APIClient
from .auth_storage import AuthStorage
from .config import TOKEN_MAX_AGE


class Auth:
    """Main authentication manager"""
    def __init__(self):
        self.api = APIClient()
        self.storage = AuthStorage()

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        auth_data = self.storage.load()

        if not auth_data or not auth_data.get("token"):
            return False

        # Check if token needs revalidation (> 2 hours old)
        saved_at = auth_data.get("saved_at", 0)
        if time.time() - saved_at > TOKEN_MAX_AGE:
            # Revalidate with server
            user_info = self.api.get_user_info(
                auth_data["token"],
                auth_data.get("tenant_code")
            )

            if not user_info:
                # Token invalid, clear auth
                self.storage.clear()
                return False

            # Token valid, update saved_at timestamp
            self.storage.save(
                username=auth_data["username"],
                token=auth_data["token"],
                tenant_code=auth_data.get("tenant_code"),
                user_info=user_info
            )

        return True

    def login(self, username: str, password: str) -> bool:
        """Authenticate user with provided credentials"""
        # Call login API
        login_result = self.api.login(username, password)
        if not login_result or not login_result.get("token"):
            return False

        token = login_result.get("token")
        tenant_code = login_result.get("tenantCode")

        # Get user info
        user_info = self.api.get_user_info(token, tenant_code)
        if not user_info:
            return False

        # Save to storage
        return self.storage.save(username, token, tenant_code, user_info)

    def logout(self) -> bool:
        """
        Logout user

        Returns:
            True if logout successful
        """
        if self.storage.clear():
            print("Logged out successfully")
            return True
        return False

    def get_user_info(self) -> Optional[dict]:
        """
        Get current user info from storage
        """
        auth_data = self.storage.load()
        if auth_data:
            return auth_data.get("user")
        return None

