""" config.py

A simple configuration file
for AitoCoder authentication
"""
import os
from pathlib import Path

# Base configuration
BASE_URL = "https://aitocoder.com/platform/api"
TIMEOUT = 30

# Web API endpoints
ENDPOINTS = {
    "login": "/login",
    "get_info": "/getInfo",
    "generate_api_key": "/llm/user/api-key/generate",
    "get_models": "/llm/user/models",
}

# Storage paths
CONFIG_DIR = Path.home() / ".auto-coder"
AUTH_FILE = CONFIG_DIR / ".ac_auth.json"
KEYS_DIR = CONFIG_DIR / "keys"
MODELS_FILE = KEYS_DIR / "models.json"
API_KEY_FILE = KEYS_DIR / "api_key.json"

# Cache settings
MEMORY_CACHE_TTL = 300  # 5 minutes
TOKEN_MAX_AGE = 7200    # 2 hours before revalidation


def get_endpoint_url(endpoint: str) -> str:
    """Get full URL for an endpoint"""
    return f"{BASE_URL.rstrip('/')}{ENDPOINTS.get(endpoint, '')}"


def ensure_config_dir():
    """Ensure config directory exists"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Set directory permissions to user-only
    os.chmod(CONFIG_DIR, 0o700)


def ensure_keys_dir():
    """Ensure keys directory exists"""
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    # Set directory permissions to user-only
    os.chmod(KEYS_DIR, 0o700)
