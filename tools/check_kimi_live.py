"""Live OpenRouter test for Kimi brainstorming parsing.

Usage:
  C:\ProgramData\anaconda3\python.exe tools/check_kimi_live.py
  C:\ProgramData\anaconda3\python.exe tools/check_kimi_live.py --ideas 2
  C:\ProgramData\anaconda3\python.exe tools/check_kimi_live.py --prompt "Your research request"
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.openrouter_client import OpenRouterClient  # noqa: E402
from config.settings import Settings  # noqa: E402
from core.member import CouncilMember  # noqa: E402
from prompts.diverge_prompts import DIVERGE_SYSTEM_PROMPT, build_diverge_prompt  # noqa: E402


def build_paths() -> tuple[Path, Path]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outputs_dir = ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    raw_json = outputs_dir / f"kimi_live_raw_{timestamp}.json"
    parsed_json = outputs_dir / f"kimi_live_parsed_{timestamp}.json"
    return raw_json, parsed_json


async def run_live_test(user_prompt: str, ideas: int, max_tokens: int, temperature: float) -> dict:
    settings = Settings()
    api_key = settings.openrouter_api_key
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not found in environment or .env")

    model_config = settings.get_model_config("kimi")
    if not model_config:
        raise RuntimeError("Kimi model config not found in config/models.yaml")

    prompt = build_diverge_prompt(
        user_prompt=user_prompt,
        user_profile=settings.get_user_profile(),
        ideas_per_member=ideas,
        is_reasoning_model=bool(model_config.get("is_reasoning_model", False)),
    )

    messages = [
        {"role": "system", "content": DIVERGE_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    client = OpenRouterClient(
        api_key=api_key,
        timeout=settings.request_timeout,
        max_retries=settings.max_retries,
    )

    response = await client.chat_completion(
        model=model_config["openrouter_id"],
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    extracted = client.extract_content(response)
    usage = client.extract_usage(response)

    member = CouncilMember(
        member_id="kimi_live",
        model_config=model_config,
        api_client=client,
    )
    ideas_parsed = member._parse_ideas(extracted)

    message = response.get("choices", [{}])[0].get("message", {})
    debug = {
        "model": model_config["openrouter_id"],
        "usage": usage,
        "message_content_is_null": message.get("content") is None,
        "has_reasoning": bool(message.get("reasoning")),
        "reasoning_details_count": len(message.get("reasoning_details", []) or []),
        "extracted_text_preview": extracted[:1000],
        "parsed_ideas_count": len(ideas_parsed),
        "parsed_ideas": ideas_parsed,
    }

    return {
        "response": response,
        "debug": debug,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a live OpenRouter Kimi brainstorming parser check.")
    parser.add_argument(
        "--prompt",
        default="Generate lightweight, feasible student research ideas for a public health time-series dataset using classical machine learning and feature engineering.",
        help="Research request to send to Kimi.",
    )
    parser.add_argument("--ideas", type=int, default=2, help="Number of idea blocks to request.")
    parser.add_argument("--max-tokens", type=int, default=1600, help="Max tokens for the response.")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature.")
    args = parser.parse_args()

    raw_json_path, parsed_json_path = build_paths()
    result = asyncio.run(
        run_live_test(
            user_prompt=args.prompt,
            ideas=args.ideas,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
    )

    raw_json_path.write_text(json.dumps(result["response"], indent=2, ensure_ascii=True), encoding="utf-8")
    parsed_json_path.write_text(json.dumps(result["debug"], indent=2, ensure_ascii=True), encoding="utf-8")

    debug = result["debug"]
    print(f"Saved raw response to: {raw_json_path}")
    print(f"Saved parsed debug to: {parsed_json_path}")
    print(f"Model: {debug['model']}")
    print(f"Usage: {debug['usage']}")
    print(f"message.content is null: {debug['message_content_is_null']}")
    print(f"has reasoning: {debug['has_reasoning']}")
    print(f"reasoning_details_count: {debug['reasoning_details_count']}")
    print(f"parsed_ideas_count: {debug['parsed_ideas_count']}")
    print("=" * 80)
    for index, idea in enumerate(debug["parsed_ideas"], 1):
        print(f"IDEA {index}")
        for key in ("title", "summary", "methodology", "feasibility", "timeline", "expected_outcomes"):
            print(f"{key}: {idea.get(key, '')}")
        print("-" * 80)


if __name__ == "__main__":
    main()
