from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import PROVIDER_API_KEYS, configured_provider_names, make_provider, resolve_provider_name
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
TRANSCRIPTS_DIR = ROOT / "transcripts"
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
DEFAULT_MODELS = {"gemini": "gemini-3.5-flash-lite"}

st.set_page_config(page_title="Research Agent v0", page_icon="🔎", layout="wide")
st.markdown(
    """
    <style>
    .block-container {max-width: 1200px; padding-top: 2rem}
    [data-testid="stMetricValue"] {font-size: 1.05rem}
    .muted {color: #64748b; font-size: .9rem}
    </style>
    """,
    unsafe_allow_html=True,
)


def new_session(
    version: str,
    requested_provider: str,
    provider_name: str,
    model: str | None,
    history_window: int,
    max_tool_rounds: int,
) -> None:
    artifact = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join((safe_slug(version), safe_slug(provider_name), timestamp))
    st.session_state.history = []
    st.session_state.turns = []
    st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact),
        "requested_provider": requested_provider,
        "provider": provider_name,
        "provider_fallback": requested_provider != provider_name,
        "model": model or getattr(make_provider(provider_name), "default_model", None),
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": st.session_state.turns,
    }


def render_trace(turn: dict[str, Any]) -> None:
    rounds = turn.get("rounds") or []
    if not rounds:
        return
    with st.expander(f"Tool trace · {len(rounds)} round(s)", expanded=False):
        for round_record in rounds:
            st.markdown(f"**Round {round_record.get('round')}**")
            calls = round_record.get("tool_calls") or []
            results = round_record.get("tool_results") or []
            if not calls:
                st.caption("Không gọi tool — agent trả lời trực tiếp.")
            for index, call in enumerate(calls):
                result = results[index].get("result", {}) if index < len(results) else {}
                error = result.get("error") if isinstance(result, dict) else None
                st.markdown(f"`{call.get('name')}` · {'❌ error' if error else '✅ completed'}")
                left, right = st.columns(2)
                left.caption("Arguments")
                left.json(call.get("args") or {})
                right.caption("Result")
                right.json(result)


def load_evidence() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    runs: list[dict[str, Any]] = []
    for path in sorted((ROOT / "runs").glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            summary = data.get("summary") or {}
            runs.append({
                "file": path.name,
                "version": data.get("version"),
                "artifact_version": data.get("artifact_version"),
                "case_accuracy": summary.get("case_accuracy"),
                "routing_accuracy": summary.get("tool_routing_accuracy"),
                "argument_accuracy": summary.get("argument_accuracy"),
                "provider_errors": summary.get("provider_error_cases"),
            })
        except (OSError, json.JSONDecodeError):
            continue

    transcripts: list[dict[str, Any]] = []
    for path in sorted(TRANSCRIPTS_DIR.glob("*.transcript.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            transcripts.append({
                "file": path.name,
                "version": data.get("version"),
                "artifact_version": data.get("artifact_version"),
                "provider": data.get("provider"),
                "turns": len(data.get("turns") or []),
                "updated_at": data.get("updated_at"),
            })
        except (OSError, json.JSONDecodeError):
            continue
    return runs, transcripts


st.title("🔎 Research Agent")
st.caption("Baseline v0 · chat thật, tool thật, trace và transcript đầy đủ")

with st.sidebar:
    st.header("Cấu hình")
    provider_options = list(PROVIDER_API_KEYS)
    configured = configured_provider_names()
    default_provider = configured[0] if configured else "openrouter"
    requested_provider = st.selectbox(
        "Model provider",
        provider_options,
        index=provider_options.index(default_provider),
    )
    try:
        provider_name = resolve_provider_name(requested_provider)
        provider_ready = True
    except RuntimeError:
        provider_name = requested_provider
        provider_ready = False
    model_input = st.text_input(
        "Model (để trống = mặc định)",
        value=DEFAULT_MODELS.get(provider_name, ""),
        key=f"model_{requested_provider}_{provider_name}",
    )
    version = st.text_input("Artifact version", "v0")
    history_window = st.slider("History window", 1, 10, 5)
    max_tool_rounds = st.slider("Max tool rounds", 1, 8, 4)
    st.caption(
        f"{'✅' if provider_ready else '⚠️'} {provider_name} key · "
        f"{'✅' if os.getenv('TAVILY_API_KEY') else '⚠️'} Tavily"
    )
    if st.button("Cuộc trò chuyện mới", width="stretch"):
        new_session(
            version,
            requested_provider,
            provider_name,
            model_input or None,
            history_window,
            max_tool_rounds,
        )
        st.rerun()

settings = (version, requested_provider, provider_name, model_input, history_window, max_tool_rounds)
if "settings" not in st.session_state or st.session_state.settings != settings:
    new_session(
        version,
        requested_provider,
        provider_name,
        model_input or None,
        history_window,
        max_tool_rounds,
    )
    st.session_state.settings = settings

artifact = st.session_state.transcript
metric_cols = st.columns(3)
metric_cols[0].metric("Version", artifact["version"])
metric_cols[1].metric("Provider", provider_name)
metric_cols[2].metric("Turns", len(st.session_state.turns))
st.markdown(
    f"<div class='muted'>Artifact: {artifact['artifact_version']}<br>"
    f"Transcript: {artifact['transcript_id']}</div>",
    unsafe_allow_html=True,
)

chat_tab, evidence_tab = st.tabs(["Chat & trace", "Run evidence"])
with chat_tab:
    if not provider_ready:
        st.warning("Chưa có model provider API key nào trong `.env`.")
    elif requested_provider != provider_name:
        st.info(f"{requested_provider} chưa được cấu hình; UI đang dùng {provider_name}.")

    for turn in st.session_state.turns:
        with st.chat_message("user"):
            st.markdown(turn["user"])
        with st.chat_message("assistant"):
            if turn.get("status") == "provider_error":
                st.error(turn.get("error", "Provider error"))
            else:
                st.markdown(turn.get("assistant_text") or "")
            render_trace(turn)

    if prompt := st.chat_input("Nhập yêu cầu nghiên cứu…", disabled=not provider_ready):
        with st.chat_message("user"):
            st.markdown(prompt)
        turn: dict[str, Any] = {
            "turn_index": len(st.session_state.turns) + 1,
            "started_at": now_iso(),
            "user": prompt,
            "status": "started",
            "assistant_text": None,
            "rounds": [],
            "tool_events": [],
        }
        try:
            system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
            tools = to_openai_tools(load_tool_declarations(TOOLS_PATH))
            messages = [
                {"role": "system", "content": system_prompt},
                *trim_history(st.session_state.history, history_window),
                {"role": "user", "content": prompt},
            ]
            with st.spinner("Agent đang nghiên cứu…"):
                result = run_model_tool_loop(
                    provider=make_provider(provider_name),
                    messages=messages,
                    tools=tools,
                    model=model_input or None,
                    max_tool_rounds=max_tool_rounds,
                )
            turn.update(result)
            st.session_state.history.extend((
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": result["assistant_text"]},
            ))
        except Exception as exc:
            turn.update(status="provider_error", error=f"{type(exc).__name__}: {exc}")
        turn["ended_at"] = now_iso()
        st.session_state.turns.append(turn)
        st.session_state.transcript["turns"] = st.session_state.turns
        write_transcript(st.session_state.transcript_path, st.session_state.transcript)
        st.rerun()

with evidence_tab:
    runs, transcripts = load_evidence()
    st.subheader("Baseline/eval runs")
    st.dataframe(runs, width="stretch", hide_index=True) if runs else st.info("Chưa có run JSON. Chạy baseline v0 sau khi thêm model provider key.")
    st.subheader("Transcripts")
    st.dataframe(transcripts, width="stretch", hide_index=True) if transcripts else st.info("Chưa có transcript.")
