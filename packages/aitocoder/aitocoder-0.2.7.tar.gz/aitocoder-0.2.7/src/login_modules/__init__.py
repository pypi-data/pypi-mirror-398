"""
AitoCoder Authentication Module
Simple login and model management.

Usage:
    from login_modules import Auth, ModelManager

    auth = Auth()
    auth.login(username, password)

    manager = ModelManager()
    manager.initialize_models(token)
"""

from .auth_login import Auth
from .model_manager import ModelManager

__all__ = ["Auth", "ModelManager"]
