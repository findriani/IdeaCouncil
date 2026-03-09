"""
Streamlit sidebar components.
"""

import streamlit as st
from typing import Dict, Any, List, Tuple
from config.settings import settings
from utils.validator import Validator, ValidationError

def render_sidebar() -> Tuple[str, List[str], Dict[str, Any]]:
    """
    Render sidebar with configuration options.

    Returns:
        Tuple of (api_key, selected_model_keys, config_dict)
    """
    st.sidebar.title("⚙️ Configuration")

    # API Key
    st.sidebar.subheader("OpenRouter API Key")
    api_key = st.sidebar.text_input(
        "API Key",
        type="password",
        value="",
        help="Get your API key from https://openrouter.ai/keys"
    )

    # Validate API key
    api_key_valid = False
    if api_key:
        try:
            Validator.validate_api_key(api_key)
            st.sidebar.success("✓ API key configured")
            api_key_valid = True
        except ValidationError as e:
            st.sidebar.error(f"✗ {str(e)}")

    st.sidebar.divider()

    # Coordinator / Converger (always Claude Sonnet)
    st.sidebar.subheader("Coordinator & Converger")
    coordinator_config = settings.get_model_config("claude_sonnet")
    coordinator_name = coordinator_config.get("display_name", "Claude Sonnet") if coordinator_config else "Claude Sonnet"
    st.sidebar.info(f"🎯 **{coordinator_name}**\nSynthesizes all ideas and ranks top recommendations.")

    st.sidebar.divider()

    # Model Selection
    st.sidebar.subheader("Council Members")

    # Preset selection
    presets = settings.models_config.get("presets", {})
    preset_options = ["Custom"] + list(presets.keys())
    preset_labels = {
        "Custom": "Custom Selection",
        "default": f"Default ({len(presets.get('default', {}).get('models', []))} models) - Recommended",
        "budget": f"Budget ({len(presets.get('budget', {}).get('models', []))} models)",
        "premium": f"Premium ({len(presets.get('premium', {}).get('models', []))} models)"
    }

    selected_preset = st.sidebar.radio(
        "Quick Presets",
        preset_options,
        format_func=lambda x: preset_labels.get(x, x),
        index=1  # Default to "default" preset
    )

    selected_models = []

    if selected_preset == "Custom":
        # Custom model selection
        st.sidebar.write("**Select Models:**")

        available_models = settings.get_all_models()

        for model_key, model_config in available_models.items():
            display_name = model_config.get("display_name", model_key)
            pricing = model_config.get("pricing", {})
            input_price = pricing.get("input_per_1m", 0)
            output_price = pricing.get("output_per_1m", 0)

            price_str = f"${input_price:.2f}/${output_price:.2f}" if input_price > 0 or output_price > 0 else "Free"

            if st.sidebar.checkbox(
                f"{display_name} ({price_str})",
                key=f"model_{model_key}",
                value=model_key in ["claude_sonnet", "chatgpt", "gemini_pro", "kimi", "qwen", "glm"]
            ):
                selected_models.append(model_key)

    else:
        # Use preset
        preset_config = presets.get(selected_preset, {})
        selected_models = preset_config.get("models", [])

        st.sidebar.info(f"Using preset: {preset_config.get('description', '')}")
        st.sidebar.write(f"**Models ({len(selected_models)}):**")

        for model_key in selected_models:
            model_config = settings.get_model_config(model_key)
            if model_config:
                st.sidebar.write(f"• {model_config.get('display_name', model_key)}")

    # Validate selection
    models_valid = False
    if selected_models:
        try:
            Validator.validate_model_selection(selected_models, settings.get_all_models())
            st.sidebar.success(f"✓ {len(selected_models)} models selected")
            models_valid = True
        except ValidationError as e:
            st.sidebar.error(f"✗ {str(e)}")

    # Cost estimate
    if selected_models and models_valid:
        total_cost = 0.0
        for phase in ["diverge", "criticize", "converge"]:
            phase_cost = settings.calculate_estimated_cost(
                model_keys=selected_models,
                phase=phase,
                num_members=len(selected_models)
            )
            total_cost += phase_cost

        live = st.session_state.get("live_prices_applied", False)
        price_note = "live prices from OpenRouter" if live else "prices from models.yaml (fallback)"
        st.sidebar.metric(
            "Est. Cost/Iteration",
            f"${total_cost:.4f}",
            help=f"Estimated cost for one complete iteration — using {price_note}"
        )

    st.sidebar.divider()

    # Session Configuration
    st.sidebar.subheader("Session Settings")

    max_iterations = st.sidebar.slider(
        "Max Iterations",
        min_value=1,
        max_value=3,
        value=3,
        help="Maximum number of refinement iterations"
    )

    ideas_per_member = st.sidebar.slider(
        "Ideas per Member",
        min_value=2,
        max_value=5,
        value=4,
        help="Number of ideas each member generates"
    )

    top_ideas_count = st.sidebar.slider(
        "Top Recommendations",
        min_value=3,
        max_value=10,
        value=6,
        help="Number of top ideas to recommend"
    )

    verbosity = st.sidebar.select_slider(
        "Progress Detail",
        options=["Minimal", "Progress", "Full"],
        value="Progress",
        help="How much detail to show during processing"
    )

    # User Profile
    st.sidebar.divider()
    st.sidebar.subheader("User Profile")

    if st.sidebar.button("📝 Edit Profile"):
        st.session_state.show_profile_editor = True

    # Show profile summary
    profile = settings.get_user_profile()
    interests = profile.get("research_interests", {})
    primary_fields = interests.get("primary_fields", [])

    if primary_fields:
        st.sidebar.write(f"**Fields:** {', '.join(primary_fields[:2])}")

    config = {
        "max_iterations": max_iterations,
        "ideas_per_member": ideas_per_member,
        "top_ideas_count": top_ideas_count,
        "verbosity": verbosity,
        "api_key_valid": api_key_valid,
        "models_valid": models_valid
    }

    return api_key, selected_models, config


def render_profile_editor():
    """Render user profile editor in modal/expander."""
    st.subheader("Edit User Profile")

    profile = settings.get_user_profile()

    # Research Interests
    st.write("**Research Interests**")
    primary_fields = st.text_area(
        "Primary Fields (comma-separated)",
        value=", ".join(profile.get("research_interests", {}).get("primary_fields", [])),
        help="Your main research areas"
    )

    specific_topics = st.text_area(
        "Specific Topics (comma-separated)",
        value=", ".join(profile.get("research_interests", {}).get("specific_topics", [])),
        help="Specific topics of interest"
    )

    # Constraints
    st.write("**Constraints**")
    timeline = st.text_input(
        "Timeline",
        value=", ".join(profile.get("constraints", {}).get("timeline", [])),
        help="e.g., 'Thesis duration: 6 months'"
    )

    expertise = st.text_input(
        "Expertise Level",
        value=", ".join(profile.get("constraints", {}).get("expertise", [])),
        help="e.g., 'Undergraduate level'"
    )

    # Goals
    st.write("**Goals**")
    primary_goal = st.text_input(
        "Primary Goal",
        value=profile.get("goals", {}).get("primary", ""),
        help="Main research goal"
    )

    col1, col2 = st.columns(2)

    if col1.button("Save Profile", type="primary"):
        # Update profile
        updated_profile = profile.copy()
        updated_profile["research_interests"]["primary_fields"] = [f.strip() for f in primary_fields.split(",") if f.strip()]
        updated_profile["research_interests"]["specific_topics"] = [t.strip() for t in specific_topics.split(",") if t.strip()]
        updated_profile["constraints"]["timeline"] = [timeline] if timeline else []
        updated_profile["constraints"]["expertise"] = [expertise] if expertise else []
        updated_profile["goals"]["primary"] = primary_goal

        settings.update_user_profile(updated_profile)
        st.success("Profile updated!")
        st.session_state.show_profile_editor = False
        st.rerun()

    if col2.button("Cancel"):
        st.session_state.show_profile_editor = False
        st.rerun()
