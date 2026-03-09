"""
Configuration loader and manager.
Loads YAML configs and provides access to settings.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Manages application configuration."""

    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.project_root = self.config_dir.parent
        self.outputs_dir = self.project_root / "outputs"

        # Ensure outputs directory exists
        self.outputs_dir.mkdir(exist_ok=True)

        # Load configurations
        self.models_config = self._load_yaml("models.yaml")
        self.user_profile = self._load_user_profile()

        # API configuration - Handle both local .env and Streamlit Cloud secrets
        self.openrouter_api_key = self._get_api_key()
        self.openrouter_base_url = "https://openrouter.ai/api/v1"

        # Session defaults
        self.max_iterations = 3
        self.max_concurrent_requests = 5
        self.request_timeout = 60
        self.max_retries = 3

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_user_profile(self) -> Dict[str, Any]:
        """Load user profile, falling back to example if personal profile is absent."""
        for filename in ("user_profile.yaml", "user_profile.example.yaml"):
            filepath = self.config_dir / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        return {}

    def _get_api_key(self) -> str:
        """
        Get API key from environment or Streamlit secrets.

        Priority:
        1. Environment variable (local development with .env)
        2. Streamlit secrets (cloud deployment)
        3. Empty string (will prompt user)
        """
        # Try environment variable first (local development)
        api_key = os.getenv("OPENROUTER_API_KEY", "")

        if api_key:
            return api_key

        # Try Streamlit secrets (cloud deployment)
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "OPENROUTER_API_KEY" in st.secrets:
                return st.secrets["OPENROUTER_API_KEY"]
        except Exception:
            pass

        return ""

    def is_cloud_deployment(self) -> bool:
        """Check if running on Streamlit Cloud."""
        try:
            import streamlit as st
            return hasattr(st, "secrets")
        except:
            return False

    def get_model_config(self, model_key: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific model."""
        return self.models_config.get("available_models", {}).get(model_key)

    def get_all_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all available models."""
        return self.models_config.get("available_models", {})

    def get_all_phase_settings(self) -> Dict[str, Any]:
        """Get phase settings (temperature, max_tokens per phase)."""
        return self.models_config.get("phase_settings", {})

    def get_preset(self, preset_name: str) -> Optional[Dict[str, Any]]:
        """Get a model preset configuration."""
        return self.models_config.get("presets", {}).get(preset_name)

    def get_phase_settings(self, phase: str) -> Dict[str, Any]:
        """Get settings for a specific phase (diverge/criticize/converge)."""
        return self.models_config.get("phase_settings", {}).get(phase, {})

    def get_user_profile(self) -> Dict[str, Any]:
        """Get user research profile."""
        return self.user_profile

    def calculate_estimated_cost(
        self,
        model_keys: List[str],
        phase: str,
        num_members: Optional[int] = None
    ) -> float:
        """
        Calculate estimated cost for a phase.

        Args:
            model_keys: List of model keys to use
            phase: Phase name (diverge/criticize/converge)
            num_members: Number of council members (defaults to len(model_keys))

        Returns:
            Estimated cost in USD
        """
        if num_members is None:
            num_members = len(model_keys)

        phase_settings = self.get_phase_settings(phase)
        max_tokens = phase_settings.get("max_tokens", 2000)

        # Estimate input tokens based on phase
        input_tokens_estimate = {
            "diverge": 1000,
            "criticize": 3000,
            "converge": 5000
        }.get(phase, 1000)

        total_cost = 0.0

        for model_key in model_keys:
            model_config = self.get_model_config(model_key)
            if not model_config:
                continue

            pricing = model_config.get("pricing", {})
            input_cost_per_1m = pricing.get("input_per_1m", 0)
            output_cost_per_1m = pricing.get("output_per_1m", 0)

            # Calculate cost for this model
            input_cost = (input_tokens_estimate / 1_000_000) * input_cost_per_1m
            output_cost = (max_tokens / 1_000_000) * output_cost_per_1m

            # Multiply by usage count based on phase
            if phase == "diverge":
                # Each member generates once
                model_cost = (input_cost + output_cost)
            elif phase == "criticize":
                # Each member critiques once
                model_cost = (input_cost + output_cost)
            else:  # converge
                # Only one model synthesizes
                model_cost = (input_cost + output_cost) if model_key == model_keys[0] else 0

            total_cost += model_cost

        # For criticize phase, multiply by number of members
        if phase == "criticize":
            total_cost *= num_members

        return total_cost

    def validate_api_key(self) -> bool:
        """Check if API key is configured."""
        return bool(self.openrouter_api_key and self.openrouter_api_key != "your_key_here")

    def apply_live_prices(self, live_prices: Dict[str, Dict[str, float]]) -> None:
        """
        Overwrite in-memory model pricing with live data fetched from OpenRouter.
        live_prices: {openrouter_id: {input_per_1m: float, output_per_1m: float}}
        Falls back to models.yaml values for any model not found in live data.
        """
        for model_cfg in self.models_config.get("available_models", {}).values():
            openrouter_id = model_cfg.get("openrouter_id", "")
            if openrouter_id in live_prices:
                model_cfg["pricing"] = live_prices[openrouter_id]

    def update_user_profile(self, profile_data: Dict[str, Any]) -> None:
        """Update user profile with new data."""
        self.user_profile.update(profile_data)

        # Save to file
        profile_path = self.config_dir / "user_profile.yaml"
        with open(profile_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.user_profile, f, default_flow_style=False, allow_unicode=True)

# Singleton instance
settings = Settings()
