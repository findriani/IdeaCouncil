"""
Basic tests for LLM Council application.
Run with: pytest tests/test_basic.py -v
"""

import pytest
from config.settings import Settings
from utils.validator import Validator, ValidationError
from api.cost_tracker import CostTracker
from core.phase_manager import PhaseManager, Phase

def test_settings_load():
    """Test configuration loading."""
    settings = Settings()

    # Check models config loaded
    assert settings.models_config is not None
    assert "available_models" in settings.models_config
    assert "presets" in settings.models_config

    # Check user profile loaded
    assert settings.user_profile is not None
    assert "research_interests" in settings.user_profile

def test_model_config_access():
    """Test model configuration access."""
    settings = Settings()

    # Test getting a model config
    claude_config = settings.get_model_config("claude_sonnet")
    assert claude_config is not None
    assert "openrouter_id" in claude_config
    assert "display_name" in claude_config
    assert "pricing" in claude_config

    # Test getting all models
    all_models = settings.get_all_models()
    assert len(all_models) > 0

    # Test getting preset
    default_preset = settings.get_preset("default")
    assert default_preset is not None
    assert "models" in default_preset

def test_cost_estimation():
    """Test cost calculation."""
    settings = Settings()

    # Test cost calculation for diverge phase
    model_keys = ["claude_sonnet", "gemini"]
    cost = settings.calculate_estimated_cost(
        model_keys=model_keys,
        phase="diverge",
        num_members=2
    )

    assert cost >= 0
    assert isinstance(cost, float)

def test_validator_api_key():
    """Test API key validation."""
    # Valid key
    try:
        Validator.validate_api_key("sk-or-v1-abcdef123456789012345678901234567890")
        assert True
    except ValidationError:
        assert False, "Valid API key rejected"

    # Invalid keys
    with pytest.raises(ValidationError):
        Validator.validate_api_key("")

    with pytest.raises(ValidationError):
        Validator.validate_api_key("your_key_here")

    with pytest.raises(ValidationError):
        Validator.validate_api_key("short")

def test_validator_models():
    """Test model selection validation."""
    settings = Settings()
    available_models = settings.get_all_models()

    # Valid selection
    try:
        Validator.validate_model_selection(
            ["claude_sonnet", "gemini"],
            available_models
        )
        assert True
    except ValidationError:
        assert False, "Valid model selection rejected"

    # Too few models
    with pytest.raises(ValidationError):
        Validator.validate_model_selection(["claude_sonnet"], available_models)

    # Invalid model key
    with pytest.raises(ValidationError):
        Validator.validate_model_selection(
            ["claude_sonnet", "invalid_model"],
            available_models
        )

def test_validator_prompt():
    """Test prompt validation."""
    # Valid prompt
    try:
        Validator.validate_user_prompt("I need research ideas for machine learning")
        assert True
    except ValidationError:
        assert False, "Valid prompt rejected"

    # Empty prompt
    with pytest.raises(ValidationError):
        Validator.validate_user_prompt("")

    # Too short
    with pytest.raises(ValidationError):
        Validator.validate_user_prompt("ML ideas")

    # Too long
    with pytest.raises(ValidationError):
        Validator.validate_user_prompt("x" * 6000)

def test_cost_tracker():
    """Test cost tracking."""
    tracker = CostTracker()

    # Log a request
    cost = tracker.log_request(
        model="claude-3.5-sonnet",
        phase="diverge",
        member_id="member_1",
        input_tokens=1000,
        output_tokens=2000,
        input_cost_per_1m=3.0,
        output_cost_per_1m=15.0
    )

    # Check cost calculation
    expected_cost = (1000 / 1_000_000) * 3.0 + (2000 / 1_000_000) * 15.0
    assert abs(cost - expected_cost) < 0.0001

    # Check total cost
    assert abs(tracker.get_total_cost() - expected_cost) < 0.0001

    # Check cost by phase
    by_phase = tracker.get_cost_by_phase()
    assert "diverge" in by_phase
    assert abs(by_phase["diverge"] - expected_cost) < 0.0001

    # Check cost by model
    by_model = tracker.get_cost_by_model()
    assert "claude-3.5-sonnet" in by_model

def test_phase_manager():
    """Test phase management."""
    manager = PhaseManager(max_iterations=3)

    # Start iteration
    manager.start_iteration()
    assert manager.get_current_iteration() == 1
    assert manager.get_current_phase() == Phase.DIVERGE

    # Advance phases
    manager.advance_phase()
    assert manager.get_current_phase() == Phase.CRITICIZE

    manager.advance_phase()
    assert manager.get_current_phase() == Phase.CONVERGE

    manager.advance_phase()
    assert manager.get_current_phase() is None
    assert manager.is_iteration_complete()

    # Check can iterate
    assert manager.can_iterate()

    # Start another iteration
    manager.start_iteration()
    assert manager.get_current_iteration() == 2

    # Test max iterations
    manager.start_iteration()  # 3rd iteration
    assert manager.get_current_iteration() == 3

    manager.advance_phase()
    manager.advance_phase()
    manager.advance_phase()

    assert not manager.can_iterate()

def test_sanitize_filename():
    """Test filename sanitization."""
    # Test with special characters
    result = Validator.sanitize_filename("research<>ideas?*.txt")
    assert "<" not in result
    assert ">" not in result
    assert "?" not in result
    assert "*" not in result

    # Test with spaces
    result = Validator.sanitize_filename("my research ideas.txt")
    assert " " not in result
    assert "_" in result

    # Test long filename
    long_name = "x" * 300
    result = Validator.sanitize_filename(long_name)
    assert len(result) <= 200

    # Test empty filename
    result = Validator.sanitize_filename("")
    assert result == "untitled"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
