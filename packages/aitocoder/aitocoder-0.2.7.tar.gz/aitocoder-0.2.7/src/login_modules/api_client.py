"""
API client for server communication
"""
import requests
from typing import Optional, Dict, Any, List
from .config import get_endpoint_url, TIMEOUT


class APIClient:
    """Handles all API communication with the server"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AitoCoder/2.0.0'
        })

    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with server

        Returns:
            {"token": "...", "tenantCode": "..."} on success, None on failure
        """
        try:
            response = self.session.post(
                get_endpoint_url("login"),
                json={"username": username, "password": password},
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    return data.get("data")

            return None

        except requests.exceptions.RequestException as e:
            print(f"Login failed: {e}")
            return None

    def get_user_info(self, token: str, tenant_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Validate token and get user info"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            if tenant_code:
                headers["tenant_code"] = tenant_code
                headers["token"] = token

            response = self.session.get(
                get_endpoint_url("get_info"),
                headers=headers,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    return data.get("data")

            return None

        except requests.exceptions.RequestException as e:
            print(f"Token validation failed: {e}")
            return None

    def generate_api_key(self, token: str) -> Optional[Dict[str, Any]]:
        """Generate API key from server"""
        try:
            headers = {"Authorization": f"Bearer {token}"}

            response = self.session.post(
                get_endpoint_url("generate_api_key"),
                headers=headers,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    return data.get("data")

            return None

        except requests.exceptions.RequestException as e:
            print(f"API key generation failed: {e}")
            return None

    def get_models(self, token: str) -> Optional[List[Dict[str, Any]]]:
        """Get available models from server"""
        try:
            headers = {"Authorization": f"Bearer {token}"}

            response = self.session.get(
                get_endpoint_url("get_models"),
                headers=headers,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    return data.get("data", [])

            return None

        except requests.exceptions.RequestException as e:
            print(f"Failed to get models: {e}")
            return None
