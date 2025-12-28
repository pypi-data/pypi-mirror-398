"""model_manager.py

Model and API key management
"""
import json
import os
from typing import Optional, Dict, Any, List
from .config import MODELS_FILE, API_KEY_FILE, ensure_keys_dir
from .api_client import APIClient


class ModelManager:
    """Manages model configurations and API keys"""

    def __init__(self):
        ensure_keys_dir()
        self.api_client = APIClient()

    def generate_and_save_api_key(self, token: str) -> Optional[Dict[str, str]]:
        """
        Generate API key from server and save it
        Returns {"api_key": "...", "base_url": "..."} on success, None on failure
        """
        # Check if API key already exists
        existing = self.load_api_key()
        if existing:
            print("\u2713 Using existing API key")
            return existing

        # Generate new API key
        result = self.api_client.generate_api_key(token)

        if not result:
            print("Failed to generate API key")
            return None

        api_key = result.get("apiKey")
        base_url = result.get("baseUrl")

        if not api_key or not base_url:
            print("Invalid API key response")
            return None

        # Save API key
        api_key_data = {
            "api_key": api_key,
            "base_url": base_url
        }

        if self._save_api_key(api_key_data):
            print("\u2713 API key saved")
            return api_key_data

        return None

    def get_and_save_models(self, token: str, api_key: str, base_url: str) -> bool:
        """Get models from server and save to models.json """
        models = self.api_client.get_models(token)

        if not models:
            print("Failed to fetch models")
            return False

        # Transform models to autocoder format
        autocoder_models = self._transform_models(models, api_key, base_url)

        # Save to models.json
        if self._save_models(autocoder_models):
            return True

        return False

    def load_api_key(self) -> Optional[Dict[str, str]]:
        """
        Load API key from file

        Returns:
            {"api_key": "...", "base_url": "..."} or None
        """
        try:
            if API_KEY_FILE.exists():
                with open(API_KEY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Failed to load API key: {e}")
        return None

    def load_models(self) -> List[Dict[str, Any]]:
        """
        Load models from file

        Returns:
            List of model dicts
        """
        try:
            if MODELS_FILE.exists():
                with open(MODELS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Failed to load models: {e}")
        return []

    def _save_api_key(self, api_key_data: Dict[str, str]) -> bool:
        """Save API key to file"""
        try:
            with open(API_KEY_FILE, 'w', encoding='utf-8') as f:
                json.dump(api_key_data, f, indent=2)
            os.chmod(API_KEY_FILE, 0o600)
            return True
        except Exception as e:
            print(f"Failed to save API key: {e}")
            return False

    def _save_models(self, models: List[Dict[str, Any]]) -> bool:
        """
        Save models to file, merging with existing models

        Args:
            models: List of model dicts

        Returns:
            True if successful
        """
        try:
            # Load existing models
            existing_models = self.load_models()

            # Create a map of existing models by name
            existing_map = {m.get("name"): m for m in existing_models}

            # Update existing models and add new ones
            updated_models = []
            new_model_names = set()

            for new_model in models:
                model_name = new_model.get("name")
                new_model_names.add(model_name)

                if model_name in existing_map:
                    # Update existing model
                    existing_model = existing_map[model_name]
                    # Keep api_key if it exists
                    api_key = existing_model.get("api_key")
                    existing_model.update(new_model)
                    if api_key:
                        existing_model["api_key"] = api_key
                    updated_models.append(existing_model)
                else:
                    # Add new model
                    updated_models.append(new_model)

            # Keep old models that aren't in the new list (preserve user's models)
            for existing_model in existing_models:
                if existing_model.get("name") not in new_model_names:
                    updated_models.append(existing_model)

            # Save to file
            with open(MODELS_FILE, 'w', encoding='utf-8') as f:
                json.dump(updated_models, f, indent=2, ensure_ascii=False)

            os.chmod(MODELS_FILE, 0o600)
            return True

        except Exception as e:
            print(f"Failed to save models: {e}")
            return False

    def _transform_models(self, api_models: List[Dict[str, Any]],
                         api_key: str, base_url: str) -> List[Dict[str, Any]]:
        """
        Transform API model format to autocoder format

        Args:
            api_models: Models from API
            api_key: API key to set for all models
            base_url: Base URL for API

        Returns:
            List of transformed models
        """
        autocoder_models = []

        for model in api_models:
            autocoder_model = {
                "name": model.get("displayName", ""),
                "description": model.get("description", ""),
                "model_name": model.get("modelName", model.get("name", "")),
                "model_type": "saas/openai",
                "context_window": int(model.get("contextLength", 8096)),
                "base_url": base_url,
                "is_reasoning": model.get("isReasoning", False),
                "input_price": float(model.get("inputPrice", 0.0)) * 1000,  # API uses per-k pricing
                "output_price": float(model.get("outputPrice", 0.0)) * 1000,
                "average_speed": 0.0,
                "max_output_tokens": int(model.get("maxTokens", 8096)),
                "api_key": api_key  # Set API key for each model
            }
            autocoder_models.append(autocoder_model)

        return autocoder_models

    def update_model_api_keys(self, api_key: str) -> bool:
        """Update API key for all models"""
        try:
            models = self.load_models()

            # Update API key for all models
            for model in models:
                model["api_key"] = api_key

            # Save back
            with open(MODELS_FILE, 'w', encoding='utf-8') as f:
                json.dump(models, f, indent=2, ensure_ascii=False)

            print(f"Updated API key for {len(models)} models")
            return True

        except Exception as e:
            print(f"Failed to update model API keys: {e}")
            return False

    def initialize_models(self, token: str) -> bool:
        """Complete model initialization: generate API key and fetch models"""
        # Generate/load API key
        api_key_data = self.generate_and_save_api_key(token)
        if not api_key_data:
            return False

        api_key = api_key_data["api_key"]
        base_url = api_key_data["base_url"]

        # Fetch and save models
        if not self.get_and_save_models(token, api_key, base_url):
            return False

        print("\u2713 Models initialized")
        return True

    def get_model_info(self) -> Dict[str, Any]:
        """Get summary of model configuration"""
        models = self.load_models()
        api_key_data = self.load_api_key()

        return {
            "model_count": len(models),
            "has_api_key": api_key_data is not None,
            "base_url": api_key_data.get("base_url") if api_key_data else None,
            "models": [m.get("name") for m in models]
        }
