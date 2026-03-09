"""
Input validation utilities.
"""

from typing import List, Dict, Any, Optional
import re

class ValidationError(Exception):
    """Custom validation error."""
    pass

class Validator:
    """Input validation helper."""

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """
        Validate OpenRouter API key format.

        Args:
            api_key: API key string

        Returns:
            True if valid format

        Raises:
            ValidationError: If invalid
        """
        if not api_key or api_key.strip() == "":
            raise ValidationError("API key cannot be empty")

        if api_key == "your_key_here":
            raise ValidationError("Please replace placeholder API key with your actual key")

        if len(api_key) < 20:
            raise ValidationError("API key appears too short")

        return True

    @staticmethod
    def validate_model_selection(model_keys: List[str], available_models: Dict[str, Any]) -> bool:
        """
        Validate selected models.

        Args:
            model_keys: List of selected model keys
            available_models: Dictionary of available models

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if not model_keys or len(model_keys) < 2:
            raise ValidationError("Please select at least 2 models for the council")

        if len(model_keys) > 10:
            raise ValidationError("Maximum 10 models allowed to avoid excessive costs")

        for key in model_keys:
            if key not in available_models:
                raise ValidationError(f"Invalid model key: {key}")

        return True

    @staticmethod
    def validate_user_prompt(prompt: str) -> bool:
        """
        Validate user research prompt.

        Args:
            prompt: User input prompt

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if not prompt or prompt.strip() == "":
            raise ValidationError("Research prompt cannot be empty")

        if len(prompt.strip()) < 10:
            raise ValidationError("Please provide a more detailed prompt (at least 10 characters)")

        if len(prompt) > 5000:
            raise ValidationError("Prompt too long (max 5000 characters)")

        return True

    @staticmethod
    def validate_iteration_count(count: int, max_iterations: int = 3) -> bool:
        """
        Validate iteration count.

        Args:
            count: Current iteration count
            max_iterations: Maximum allowed iterations

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if count >= max_iterations:
            raise ValidationError(f"Maximum {max_iterations} iterations reached")

        if count < 0:
            raise ValidationError("Invalid iteration count")

        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe file system use.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)

        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')

        # Limit length
        if len(sanitized) > 200:
            sanitized = sanitized[:200]

        return sanitized or "untitled"
