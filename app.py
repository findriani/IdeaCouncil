"""
LLM Council Research Brainstorming Application
Main Streamlit application.
"""

import streamlit as st
import asyncio
from pathlib import Path
from typing import Optional

# Import core modules
from config.settings import settings
from api.openrouter_client import OpenRouterClient, OpenRouterError, InsufficientCreditsError, ModelNotAvailableError
from api.rate_limiter import RateLimiter
from api.cost_tracker import CostTracker
from core.council import Council
from utils.logger import logger
from utils.validator import Validator, ValidationError
from utils.report_generator import ReportGenerator
from utils.context_manager import ContextManager

# Import UI components
from ui.sidebar import render_sidebar, render_profile_editor
from ui.progress_display import ProgressDisplay, display_phase_results
from ui.report_viewer import display_report, display_quick_summary, display_refinement_section

# Page configuration
st.set_page_config(
    page_title="IdeaCouncil",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "council" not in st.session_state:
        st.session_state.council = None

    if "iteration_count" not in st.session_state:
        st.session_state.iteration_count = 0

    if "results_history" not in st.session_state:
        st.session_state.results_history = []

    if "user_prompt" not in st.session_state:
        st.session_state.user_prompt = ""

    if "show_profile_editor" not in st.session_state:
        st.session_state.show_profile_editor = False

    if "qa_history" not in st.session_state:
        st.session_state.qa_history = []

    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    if "selected_models" not in st.session_state:
        st.session_state.selected_models = []

    if "cost_tracker" not in st.session_state:
        st.session_state.cost_tracker = CostTracker()

    if "context_manager" not in st.session_state:
        st.session_state.context_manager = ContextManager()


async def run_iteration_async(
    council: Council,
    user_prompt: str,
    user_feedback: str,
    progress_display: ProgressDisplay
):
    """
    Run one iteration asynchronously.

    Args:
        council: Council instance
        user_prompt: User research prompt
        user_feedback: User feedback for refinement
        progress_display: Progress display instance

    Returns:
        Iteration results
    """
    def progress_callback(update_type: str, message: str):
        progress_display.update(update_type, message)

    results = await council.run_iteration(
        user_prompt=user_prompt,
        user_feedback=user_feedback,
        progress_callback=progress_callback
    )

    return results


def run_iteration(
    council: Council,
    user_prompt: str,
    user_feedback: str = "",
    verbosity: str = "Progress"
):
    """
    Run one iteration (sync wrapper for async function).

    Args:
        council: Council instance
        user_prompt: User research prompt
        user_feedback: User feedback for refinement
        verbosity: Progress verbosity level
    """
    progress_display = ProgressDisplay(verbosity=verbosity)
    progress_display.start()

    try:
        # Run async iteration
        results = asyncio.run(
            run_iteration_async(
                council=council,
                user_prompt=user_prompt,
                user_feedback=user_feedback,
                progress_display=progress_display
            )
        )

        progress_display.finish()

        # Store results
        st.session_state.results_history.append(results)
        st.session_state.iteration_count += 1

        # Display phase results if verbose
        if verbosity in ["Progress", "Full"]:
            display_phase_results("Diverge", results.get("diverge", {}), verbosity)
            display_phase_results("Criticize", results.get("criticize", {}), verbosity)
            display_phase_results("Converge", results.get("converge", {}), verbosity)

        return True

    except OpenRouterError as e:
        progress_display.error(f"API Error: {str(e)}")
        logger.error(f"OpenRouter API error: {e}")
        return False

    except Exception as e:
        progress_display.error(f"Unexpected error: {str(e)}")
        logger.error(f"Unexpected error during iteration: {e}", exc_info=True)
        return False


@st.cache_data(ttl=3600)
def _fetch_openrouter_prices() -> dict:
    """
    Fetch live model pricing from OpenRouter's public models endpoint.
    Cached for 1 hour. Returns {openrouter_id: {input_per_1m, output_per_1m}}.
    OpenRouter pricing fields are per-token; multiply by 1M to normalise.
    """
    import httpx
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get("https://openrouter.ai/api/v1/models")
            resp.raise_for_status()
        prices = {}
        for model in resp.json().get("data", []):
            model_id = model.get("id", "")
            pricing = model.get("pricing", {})
            try:
                prices[model_id] = {
                    "input_per_1m":  float(pricing.get("prompt",     0)) * 1_000_000,
                    "output_per_1m": float(pricing.get("completion", 0)) * 1_000_000,
                }
            except (ValueError, TypeError):
                continue
        return prices
    except Exception:
        return {}


def _summarize_context(text: str, prompt_type: str, api_key: str) -> str:
    """
    Call Gemini 3.1 Flash Lite to summarize dataset or literature context.
    Uses a synchronous httpx call — suitable for a one-off pre-processing step.
    """
    import httpx

    if prompt_type == "literature":
        system = "You are preparing a research landscape briefing for a creative brainstorming session."
        instruction = """Produce a compact briefing covering:

1. **The Established Territory** (what is well-covered — avoid re-proposing these)
   - Dominant methods and their typical results
   - Standard datasets and evaluation protocols

2. **Why Current Work Falls Short** (context for why novelty matters)
   - Core assumptions most papers share that could be questioned
   - Evaluation or methodology weaknesses that make results hard to trust

3. **Open Terrain** (stated as observations, not prescriptions)
   - Conditions, populations, or problem framings rarely studied
   - Combinations of ideas that have not appeared together

Rules:
- Write as background context, NOT as a list of suggested research directions
- Do not use language like "future work should..." or "a promising direction is..."
- Target length: ~400 words / ~2500 characters
- A creative reader should finish this and feel informed, not instructed"""
    else:  # dataset
        system = "You are preparing a dataset briefing for a research brainstorming session."
        instruction = """Produce a structured description using this exact format:

**Dataset Name & Source:** [name, authors, year, DOI or URL]
**Purpose & Domain:** [what it was designed for; the scientific or engineering domain]
**Subjects / Samples:** [count, demographics, sampling strategy]
**Signals / Features:** [each signal or feature, type, units, sampling rate if applicable]
**Labels & Ground Truth:** [labels available, collection method, any labeling gaps or caveats]
**Data Format & Structure:** [file format, folder structure, row/column layout, preprocessing applied]
**Key Constraints & Caveats:** [missing data, quality issues, access restrictions]
**Unique Strengths:** [what makes this dataset unusual or particularly valuable]

Rules:
- Be specific: name exact column labels, signal types, sample counts
- Do not speculate about research directions — only describe what exists
- Flag any ambiguities or limitations explicitly
- Target length: ~400 words / ~2500 characters"""

    payload = {
        "model": "google/gemini-3.1-flash-lite-preview",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"{instruction}\n\nText to summarize:\n\n{text}"}
        ],
        "temperature": 0.3,
        "max_tokens": 900
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/llm-council",
        "X-Title": "LLM Council Research Brainstorming"
    }
    with httpx.Client(timeout=60) as client:
        response = client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def _ask_about_ideas(
    question: str,
    selected_idea: Optional[dict],
    iterations_data: list,
    history: list,
    api_key: str,
) -> str:
    """
    Call Gemini 3.1 Flash Lite to answer a question about the council's ideas.
    Passes previous Q&A turns as conversation history to support follow-up questions.
    """
    import httpx

    # Build a compact ideas + critiques summary as system context
    context_lines = []
    for iter_i, iteration in enumerate(iterations_data, 1):
        prefix = f"[Iteration {iter_i}] " if len(iterations_data) > 1 else ""
        for member_id, data in iteration.get("diverge", {}).items():
            for idea in data.get("ideas", []):
                idea_id = idea.get("idea_id", "?")
                context_lines.append(
                    f"{prefix}Idea {idea_id} — {idea.get('title', 'Untitled')}\n"
                    f"  Summary: {idea.get('summary', '')}\n"
                    f"  Methodology: {idea.get('methodology', '')}\n"
                    f"  Feasibility: {idea.get('feasibility', '')}"
                )
    ideas_block = "\n\n".join(context_lines) or "No ideas available."

    focus_block = ""
    if selected_idea:
        focus_block = (
            f"\n\nThe user is asking specifically about this idea:\n"
            f"Title: {selected_idea.get('title', '')}\n"
            f"Summary: {selected_idea.get('summary', '')}\n"
            f"Methodology: {selected_idea.get('methodology', '')}\n"
            f"Feasibility: {selected_idea.get('feasibility', '')}"
        )

    system = (
        "You are a knowledgeable research assistant helping a researcher understand "
        "ideas generated by an LLM brainstorming council. "
        "Answer clearly and concisely. Reference specific ideas by title when relevant."
    )

    # Build message list: system context → previous Q&A turns → current question
    messages = [
        {
            "role": "user",
            "content": (
                f"Here are the research ideas generated by the council:\n\n"
                f"{ideas_block}{focus_block}\n\n"
                "I may ask several follow-up questions about these ideas."
            ),
        },
        {"role": "assistant", "content": "Understood. I have the council's ideas in context. What would you like to know?"},
    ]
    for entry in history[-6:]:  # last 6 turns to keep context manageable
        messages.append({"role": "user",      "content": entry["question"]})
        messages.append({"role": "assistant", "content": entry["answer"]})
    messages.append({"role": "user", "content": question})

    payload = {
        "model": "google/gemini-3.1-flash-lite-preview",
        "messages": [{"role": "system", "content": system}] + messages,
        "temperature": 0.4,
        "max_tokens": 800,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/llm-council",
        "X-Title": "LLM Council Research Brainstorming",
    }
    with httpx.Client(timeout=60) as client:
        response = client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def main():
    """Main application."""
    initialize_session_state()

    # Fetch live pricing from OpenRouter once per session and apply to settings
    if not st.session_state.get("live_prices_applied"):
        live_prices = _fetch_openrouter_prices()
        if live_prices:
            settings.apply_live_prices(live_prices)
        st.session_state.live_prices_applied = bool(live_prices)

    # Header
    st.markdown('<div class="main-header">🧠 IdeaCouncil</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">A multi-LLM council that brainstorms, critiques, and ranks research ideas — so you don\'t have to choose just one perspective.</div>', unsafe_allow_html=True)

    # Sidebar
    api_key, selected_models, config = render_sidebar()

    # Store in session state
    st.session_state.api_key = api_key
    st.session_state.selected_models = selected_models

    # Profile editor (if requested)
    if st.session_state.show_profile_editor:
        render_profile_editor()
        return

    # Check if configuration is valid
    config_valid = config["api_key_valid"] and config["models_valid"]

    if not config_valid:
        st.warning("⚠️ Please configure your API key and select models in the sidebar to get started.")
        st.info("""
        **Getting Started:**
        1. Get your API key from [OpenRouter](https://openrouter.ai/keys)
        2. Enter the API key in the sidebar
        3. Select models (or use a preset)
        4. Enter your research prompt below
        """)
        return

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Research Prompt")

        user_prompt = st.text_area(
            "What research ideas are you looking for?",
            placeholder="e.g., 'I need ML research ideas for time series analysis, suitable for undergraduate thesis, no deep learning'",
            height=120,
            key="user_prompt_input",
            help="Be as specific or as vague as you like. The council will adapt to your needs."
        )

    with col2:
        st.subheader("Quick Stats")
        coordinator_cfg = settings.get_model_config("claude_sonnet")
        coordinator_name = coordinator_cfg.get("display_name", "Claude Sonnet") if coordinator_cfg else "Claude Sonnet"
        st.metric("Coordinator", coordinator_name)
        st.metric("Council Members", len(selected_models))
        st.metric("Max Iterations", config["max_iterations"])

    # Additional context section — locked after session starts
    session_active = st.session_state.iteration_count > 0
    with st.expander("📎 Additional Context (optional)", expanded=not session_active):
        if session_active:
            st.info("Context is locked for this session. Start a new session to change it.")
            ctx = st.session_state.context_manager
            tok = ctx.token_estimate()
            if not ctx.dataset.is_empty:
                st.markdown("**Dataset context in use:**")
                st.text_area("Dataset context", value=ctx.dataset.full(), height=80, disabled=True,
                             key="ctx_ds_locked", label_visibility="collapsed")
            if not ctx.literature.is_empty:
                st.markdown("**Literature context in use:**")
                st.text_area("Literature context", value=ctx.literature.full(), height=80, disabled=True,
                             key="ctx_lit_locked", label_visibility="collapsed")
            if not ctx.is_empty:
                st.caption(
                    f"Estimated tokens/call — Diverge: ~{tok['diverge']} | "
                    f"Criticize: ~{tok['criticize']} | Converge: ~{tok['converge']}"
                )
        else:
            def _context_input(
                label: str, placeholder: str, key_prefix: str,
                prompt_type: str, target_chars: int
            ) -> str:
                """Render a text+upload pair with char count and summarize button."""
                # Apply any pending summarization result BEFORE the widget renders
                pending_key = f"{key_prefix}_pending"
                success_key = f"{key_prefix}_summarized_ok"
                if pending_key in st.session_state:
                    st.session_state[f"{key_prefix}_typed"] = st.session_state.pop(pending_key)

                tab_text, tab_file = st.tabs(["✏️ Type / Paste", "📁 Upload File (.txt / .md)"])
                with tab_text:
                    typed = st.text_area(
                        label, placeholder=placeholder, height=120, key=f"{key_prefix}_typed"
                    )
                with tab_file:
                    uploaded = st.file_uploader(
                        "Upload .txt or .md", type=["txt", "md"], key=f"{key_prefix}_upload"
                    )
                    file_text = ""
                    if uploaded:
                        file_text = ContextManager._read_file(uploaded)
                        st.success(f"Loaded: {uploaded.name} ({len(file_text):,} chars)")
                        st.text_area(
                            "File preview", key=f"{key_prefix}_preview",
                            value=file_text[:400] + ("..." if len(file_text) > 400 else ""),
                            height=80, disabled=True, label_visibility="collapsed"
                        )

                current_text = (file_text or typed).strip()

                # Show success message from previous summarization run
                if st.session_state.pop(success_key, None) is not None:
                    st.success(f"✅ Summarized to {len(current_text):,} chars using Gemini Flash Lite")

                # Char count + summarize button
                if current_text:
                    char_count = len(current_text)
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        if char_count <= target_chars:
                            st.caption(f"{char_count:,} chars — ✅ within {target_chars:,}-char limit")
                        else:
                            st.caption(f"{char_count:,} chars — ⚠️ over {target_chars:,}-char limit, consider summarizing")
                    with col_btn:
                        if st.button("✨ Summarize", key=f"{key_prefix}_summarize_btn",
                                     use_container_width=True):
                            if not st.session_state.get("api_key"):
                                st.warning("Enter your API key first.")
                            else:
                                with st.spinner("Summarizing with Gemini Flash Lite..."):
                                    try:
                                        summary = _summarize_context(
                                            current_text, prompt_type,
                                            st.session_state.api_key
                                        )
                                        st.session_state[f"{key_prefix}_pending"] = summary
                                        st.session_state[success_key] = len(summary)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Summarization failed: {e}")

                return current_text

            st.markdown("#### 1. Dataset Description")
            dataset_raw = _context_input(
                label="Describe your dataset (size, features, target, format...)",
                placeholder=(
                    "Example:\n"
                    "Dataset: Alzheimer's MRI — 10,880 images, 4 classes\n"
                    "- Classes: NonDemented, VeryMild, Mild, ModerateDemented\n"
                    "- Format: 224×224 PNG, already augmented\n"
                    "- Source: Kaggle (public)"
                ),
                key_prefix="dataset",
                prompt_type="dataset",
                target_chars=2500
            )

            st.markdown("#### 2. Related Literature")
            literature_raw = _context_input(
                label="Paste key papers, known approaches, or a short related-work summary...",
                placeholder=(
                    "Example:\n"
                    "- Smith et al. (2023): CNN-based Alzheimer's classification, 94% accuracy on same dataset\n"
                    "- Jones et al. (2022): GLCM + SVM, 87% accuracy, no explainability\n"
                    "- Gap: no lightweight pipeline suitable for low-resource settings"
                ),
                key_prefix="literature",
                prompt_type="literature",
                target_chars=2500
            )

            # Build context manager and show token estimate
            new_ctx = ContextManager(dataset=dataset_raw, literature=literature_raw)
            st.session_state.context_manager = new_ctx
            if not new_ctx.is_empty:
                tok = new_ctx.token_estimate()
                st.caption(
                    f"Estimated tokens/call — Diverge: ~{tok['diverge']} | "
                    f"Criticize: ~{tok['criticize']} | Converge: ~{tok['converge']}"
                )

    # Action buttons
    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 2])

    with col_btn1:
        start_button = st.button(
            "🚀 Start Brainstorming",
            type="primary",
            disabled=not user_prompt or st.session_state.iteration_count > 0,
            use_container_width=True
        )

    with col_btn2:
        new_session_button = st.button(
            "🔄 New Session",
            disabled=st.session_state.iteration_count == 0,
            use_container_width=True
        )

    # Handle start button
    if start_button and user_prompt:
        try:
            # Validate prompt
            Validator.validate_user_prompt(user_prompt)

            # Initialize council
            rate_limiter = RateLimiter(
                max_concurrent=settings.max_concurrent_requests,
                requests_per_minute=20
            )

            api_client = OpenRouterClient(
                api_key=api_key,
                base_url=settings.openrouter_base_url,
                timeout=settings.request_timeout,
                max_retries=settings.max_retries,
                rate_limiter=rate_limiter
            )

            council = Council(
                model_configs=settings.get_all_models(),
                selected_model_keys=selected_models,
                api_client=api_client,
                cost_tracker=st.session_state.cost_tracker,
                user_profile=settings.get_user_profile(),
                max_iterations=config["max_iterations"],
                ideas_per_member=config["ideas_per_member"],
                top_ideas_count=config["top_ideas_count"],
                context_manager=st.session_state.context_manager,
                phase_settings=settings.get_all_phase_settings()
            )

            st.session_state.council = council

            # Run first iteration
            success = run_iteration(
                council=council,
                user_prompt=user_prompt,
                user_feedback="",
                verbosity=config["verbosity"]
            )

            if success:
                st.rerun()

        except ValidationError as e:
            st.error(f"Validation Error: {str(e)}")

        except Exception as e:
            st.error(f"Error initializing council: {str(e)}")
            logger.error(f"Council initialization error: {e}", exc_info=True)

    # Handle new session button
    if new_session_button:
        st.session_state.council = None
        st.session_state.iteration_count = 0
        st.session_state.results_history = []
        st.session_state.qa_history = []
        st.session_state.cost_tracker.reset()
        st.rerun()

    # Display results if available
    if st.session_state.results_history:
        st.divider()

        # Quick summary
        display_quick_summary(st.session_state.results_history)

        # Refinement section
        if st.session_state.council and st.session_state.council.can_iterate():
            st.divider()

            user_feedback = display_refinement_section(
                can_iterate=True,
                current_iteration=st.session_state.iteration_count,
                max_iterations=config["max_iterations"]
            )

            if st.button("▶️ Run Next Iteration", type="primary", disabled=not user_feedback):
                success = run_iteration(
                    council=st.session_state.council,
                    user_prompt=user_prompt,
                    user_feedback=user_feedback,
                    verbosity=config["verbosity"]
                )

                if success:
                    st.rerun()

        # Full report
        st.divider()

        # Generate report
        report_generator = ReportGenerator(output_dir=settings.outputs_dir)
        cost_summary = st.session_state.cost_tracker.get_summary()

        model_names = [
            settings.get_model_config(m).get("display_name", m)
            for m in selected_models
            if settings.get_model_config(m)
        ]

        full_report = report_generator.generate_report(
            user_prompt=user_prompt,
            iterations_data=st.session_state.results_history,
            total_cost=cost_summary["total_cost"],
            cost_breakdown=cost_summary,
            selected_models=model_names
        )

        recommendations_report = report_generator.generate_recommendations_report(
            user_prompt=user_prompt,
            iterations_data=st.session_state.results_history,
            total_cost=cost_summary["total_cost"],
            selected_models=model_names
        )

        # Display report
        display_report(
            report_content=full_report,
            recommendations_content=recommendations_report,
            cost_summary=cost_summary,
            iterations_data=st.session_state.results_history
        )

        # ── Q&A Panel ───────────────────────────────────────────────────────
        st.divider()
        st.subheader("💬 Ask About These Ideas")
        st.caption("Ask for clarification or more detail on any idea. Supports follow-up questions.")

        # Collect all ideas for the focus dropdown
        all_ideas_flat = []
        for iteration in st.session_state.results_history:
            for member_id, data in iteration.get("diverge", {}).items():
                for idea in data.get("ideas", []):
                    all_ideas_flat.append(idea)

        idea_labels = ["(All ideas)"] + [
            idea.get("title", "Untitled") for idea in all_ideas_flat
        ]

        col_sel, col_q, col_btn = st.columns([2, 4, 1])
        with col_sel:
            selected_idx = st.selectbox(
                "Focus on idea",
                options=range(len(idea_labels)),
                format_func=lambda x: idea_labels[x],
                key="qa_idea_select",
                label_visibility="collapsed",
            )
        with col_q:
            qa_question = st.text_input(
                "Question",
                placeholder="e.g. How would the feature fusion step work in practice?",
                key="qa_question_input",
                label_visibility="collapsed",
            )
        with col_btn:
            st.write("")  # vertical alignment nudge
            ask_clicked = st.button("Ask", type="primary", use_container_width=True, key="qa_ask_btn")

        if ask_clicked:
            if not qa_question.strip():
                st.warning("Enter a question first.")
            elif not st.session_state.get("api_key"):
                st.warning("Enter your API key first.")
            else:
                selected_idea = None if selected_idx == 0 else all_ideas_flat[selected_idx - 1]
                with st.spinner("Thinking..."):
                    try:
                        answer = _ask_about_ideas(
                            question=qa_question,
                            selected_idea=selected_idea,
                            iterations_data=st.session_state.results_history,
                            history=st.session_state.qa_history,
                            api_key=st.session_state.api_key,
                        )
                        st.session_state.qa_history.append({
                            "idea_label": idea_labels[selected_idx],
                            "question": qa_question,
                            "answer": answer,
                        })
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to get answer: {e}")

        # Display conversation history (newest first)
        for entry in reversed(st.session_state.qa_history):
            with st.chat_message("user"):
                idea_tag = f"**[{entry['idea_label']}]** " if entry["idea_label"] != "(All ideas)" else ""
                st.markdown(f"{idea_tag}{entry['question']}")
            with st.chat_message("assistant"):
                st.markdown(entry["answer"])

    # Footer
    st.divider()
    st.caption("IdeaCouncil — Built with Streamlit and OpenRouter API")


if __name__ == "__main__":
    main()
