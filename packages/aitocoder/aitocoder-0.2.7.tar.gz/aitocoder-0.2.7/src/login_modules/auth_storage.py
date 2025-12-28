"""
Simple auth storage with two-tier caching (memory + file)
"""
import json
import os
import time
from typing import Optional, Dict, Any
from .config import AUTH_FILE, ensure_config_dir, MEMORY_CACHE_TTL


class AuthStorage:
    """Manages auth data with memory cache and file persistence"""

    # Class-level memory cache (shared across instances)
    _memory_cache: Optional[Dict[str, Any]] = None
    _cache_time: float = 0

    def __init__(self):
        ensure_config_dir()

    def save(self, username: str, token: str, tenant_code: Optional[str] = None,
             user_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save auth data to file and cache

        Args:
            username: Username
            token: JWT token
            tenant_code: Tenant code (optional)
            user_info: User information (optional)

        Returns:
            True if saved successfully
        """
        try:
            auth_data = {
                "username": username,
                "token": token,
                "tenant_code": tenant_code,
                "user": user_info,
                "saved_at": time.time()
            }

            # Save to file
            with open(AUTH_FILE, 'w', encoding='utf-8') as f:
                json.dump(auth_data, f, indent=2)

            # Set file permissions to user-only
            os.chmod(AUTH_FILE, 0o600)

            # Update memory cache
            AuthStorage._memory_cache = auth_data
            AuthStorage._cache_time = time.time()

            return True

        except Exception as e:
            print(f"Failed to save auth: {e}")
            return False

    def load(self) -> Optional[Dict[str, Any]]:
        """
        Load auth data from cache or file

        Returns:
            Auth data dict or None if not found
        """
        # Check memory cache first (fast path)
        if AuthStorage._memory_cache and self._is_cache_valid():
            return AuthStorage._memory_cache

        # Load from file
        try:
            if AUTH_FILE.exists():
                with open(AUTH_FILE, 'r', encoding='utf-8') as f:
                    auth_data = json.load(f)

                # Update memory cache
                AuthStorage._memory_cache = auth_data
                AuthStorage._cache_time = time.time()

                return auth_data
        except Exception as e:
            print(f"Failed to load auth: {e}")

        return None

    def clear(self) -> bool:
        """Clear auth data from both cache and file"""
        try:
            # Clear memory cache
            AuthStorage._memory_cache = None
            AuthStorage._cache_time = 0

            # Remove file
            if AUTH_FILE.exists():
                AUTH_FILE.unlink()

            return True

        except Exception as e:
            print(f"Failed to clear auth: {e}")
            return False

    def _is_cache_valid(self) -> bool:
        """Check if memory cache is still valid"""
        return (time.time() - AuthStorage._cache_time) < MEMORY_CACHE_TTL

    @classmethod
    def invalidate_cache(cls):
        """Force cache invalidation (useful for testing)"""
        cls._memory_cache = None
        cls._cache_time = 0
