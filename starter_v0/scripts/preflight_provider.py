from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ARTIFACTS_DIR = ROOT / "artifacts"

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools


load_lab_env(ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test live structured tool calling.")
    parser.add_argument("--provider", choices=["openrouter", "openai", "anthropic", "gemini"], required=True)
    parser.add_argument("--model", default=None, help="Optional model override. Omit to use provider default from code.")
    parser.add_argument("--tools", type=Path, default=ARTIFACTS_DIR / "tools.yaml")
    args = parser.parse_args()

    provider = make_provider(args.provider)
    actual_provider = provider.provider_name
    model_override = None if provider.used_fallback else args.model
    selected_model = model_override or getattr(provider, "default_model", None)
    if provider.used_fallback:
        print(
            f"WARNING requested_provider={args.provider} is not configured; "
            f"using provider={actual_provider}."
        )
        if args.model:
            print(f"WARNING ignoring provider-specific model override={args.model!r}.")
    tools = to_openai_tools(load_tool_declarations(args.tools))
    messages = [
        {"role": "system", "content": "You are a tool-routing smoke test. Use tools when appropriate."},
        {"role": "user", "content": "Tweet mới nhất của Sam Altman là gì?"},
    ]
    response = provider.complete(messages, tools, model=model_override, temperature=0.0)
    if not response.tool_calls:
        raise SystemExit("Provider did not return structured tool_calls.")
    first = response.tool_calls[0]
    print(f"OK provider={actual_provider} model={selected_model}")
    print(f"tool={first.name}")
    print(f"args={first.args}")


if __name__ == "__main__":
    main()
