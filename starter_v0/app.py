"""Streamlit chat interface for the Research Agent lab."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup — make sure imports resolve from the project root
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import build_artifact_version, artifact_version_dict

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
load_lab_env(ROOT)

ARTIFACTS_DIR = ROOT / "artifacts"
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
MAX_TOOL_ROUNDS = 4
APP_VERSION = "v0"

# ---------------------------------------------------------------------------
# Helpers (adapted from chat.py)
# ---------------------------------------------------------------------------

def json_text(value: Any, *, max_chars: int | None = None) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars] + "\n...<truncated>"
    return text


def execute_tool_call(call: ToolCall) -> dict[str, Any]:
    func = TOOL_FUNCTIONS.get(call.name)
    if not func:
        return {
            "tool": call.name,
            "args": call.args,
            "result": {"error": "unknown_tool", "message": f"No local implementation for {call.name}"},
        }
    try:
        result = func(**call.args)
    except Exception as exc:
        result = {"error": type(exc).__name__, "message": str(exc)}
    return {"tool": call.name, "args": call.args, "result": result}


def tool_results_message(events: list[dict[str, Any]]) -> dict[str, str]:
    return {
        "role": "user",
        "content": (
            "TOOL_RESULTS_JSON:\n"
            f"{json_text(events, max_chars=24000)}\n\n"
            "Use only these tool results. If the user asked for a digest and the items are ready, "
            "call the formatting tool. Otherwise answer the user directly with cited sources when available."
        ),
    }


def assistant_tool_message(response_text: str | None, calls: list[ToolCall]) -> dict[str, str]:
    call_summary = [{"name": call.name, "args": call.args} for call in calls]
    content = response_text or "I will call the selected tool(s)."
    return {
        "role": "assistant",
        "content": f"{content}\n\nTOOL_CALLS_JSON:\n{json_text(call_summary)}",
    }


def run_model_tool_loop(
    *,
    provider: Any,
    messages: list[dict[str, str]],
    tools: list[dict[str, Any]],
    model: str | None,
    max_tool_rounds: int,
    status_placeholder: Any,
) -> dict[str, Any]:
    """Run the agentic tool loop, updating a Streamlit status placeholder."""
    working_messages = list(messages)
    rounds: list[dict[str, Any]] = []
    all_tool_events: list[dict[str, Any]] = []

    for round_index in range(1, max_tool_rounds + 1):
        status_placeholder.write(f"Thinking… (round {round_index})")
        response = provider.complete(working_messages, tools, model=model, temperature=0.0)
        calls = response.tool_calls
        round_record: dict[str, Any] = {
            "round": round_index,
            "assistant_text": response.text,
            "tool_calls": [{"name": c.name, "args": c.args} for c in calls],
            "tool_results": [],
        }

        if not calls:
            rounds.append(round_record)
            return {
                "status": "answered",
                "assistant_text": response.text or "",
                "rounds": rounds,
                "tool_events": all_tool_events,
            }

        working_messages.append(assistant_tool_message(response.text, calls))
        non_clarification_events: list[dict[str, Any]] = []

        for call in calls:
            status_placeholder.write(f"Calling tool: **{call.name}**")
            event = execute_tool_call(call)
            round_record["tool_results"].append(event)
            all_tool_events.append(event)

            result = event.get("result", {})
            if isinstance(result, dict) and result.get("awaiting_user"):
                question = result.get("question") or call.args.get("question") or "Please provide more information."
                rounds.append(round_record)
                return {
                    "status": "waiting_for_user",
                    "assistant_text": question,
                    "rounds": rounds,
                    "tool_events": all_tool_events,
                }

            non_clarification_events.append(event)

        rounds.append(round_record)
        working_messages.append(tool_results_message(non_clarification_events))

    return {
        "status": "max_tool_rounds",
        "assistant_text": f"Stopped after {max_tool_rounds} tool rounds.",
        "rounds": rounds,
        "tool_events": all_tool_events,
    }


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def init_state() -> None:
    if "history" not in st.session_state:
        st.session_state.history = []  # list of UI turn dicts
    if "provider_name" not in st.session_state:
        st.session_state.provider_name = "openrouter"


init_state()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("Research Agent")

    provider_name = st.selectbox(
        "Provider",
        options=["openrouter", "openai", "anthropic", "gemini"],
        index=["openrouter", "openai", "anthropic", "gemini"].index(
            st.session_state.provider_name
        ),
        key="provider_select",
    )
    st.session_state.provider_name = provider_name

    # Build artifact version label
    try:
        av = build_artifact_version(APP_VERSION, SYSTEM_PROMPT_PATH, TOOLS_PATH)
        st.caption(f"Version: `{av.artifact_version}`")
    except Exception:
        st.caption(f"Version: `{APP_VERSION}`")

    st.divider()

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# ---------------------------------------------------------------------------
# Load tools (cached so they are only read once per session)
# ---------------------------------------------------------------------------

@st.cache_resource
def get_tools():
    declarations = load_tool_declarations(TOOLS_PATH)
    return to_openai_tools(declarations)


@st.cache_data
def get_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


openai_tools = get_tools()
system_prompt = get_system_prompt()

# ---------------------------------------------------------------------------
# Chat display
# ---------------------------------------------------------------------------

st.title("Research Agent Chat")

for turn in st.session_state.history:
    # User message
    with st.chat_message("user"):
        st.markdown(turn["user"])

    # Assistant turn
    with st.chat_message("assistant"):
        # Show tool call rounds
        for round_rec in turn.get("rounds", []):
            for tc in round_rec.get("tool_calls", []):
                with st.expander(f"Tool call: `{tc['name']}`", expanded=False):
                    st.json(tc.get("args", {}))

            for tr in round_rec.get("tool_results", []):
                with st.expander(f"Tool result: `{tr['tool']}`", expanded=False):
                    result_val = tr.get("result", {})
                    if isinstance(result_val, (dict, list)):
                        st.json(result_val)
                    else:
                        st.text(str(result_val))

        # Final assistant text
        if turn.get("assistant_text"):
            st.markdown(turn["assistant_text"])

        if turn.get("status") and turn["status"] != "answered":
            st.caption(f"Status: {turn['status']}")

# ---------------------------------------------------------------------------
# User input
# ---------------------------------------------------------------------------

if user_input := st.chat_input("Ask the research agent…"):
    # Append user turn to history immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        status_area = st.empty()

        try:
            provider = make_provider(st.session_state.provider_name)

            # Build messages: system + full history context + new user message
            messages: list[dict[str, str]] = [
                {"role": "system", "content": system_prompt},
            ]
            # Add prior turns to context
            for past_turn in st.session_state.history:
                messages.append({"role": "user", "content": past_turn["user"]})
                messages.append({
                    "role": "assistant",
                    "content": past_turn.get("assistant_text") or "",
                })
            messages.append({"role": "user", "content": user_input})

            result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=None,
                max_tool_rounds=MAX_TOOL_ROUNDS,
                status_placeholder=status_area,
            )

            # Render tool call rounds
            status_area.empty()
            for round_rec in result.get("rounds", []):
                for tc in round_rec.get("tool_calls", []):
                    with st.expander(f"Tool call: `{tc['name']}`", expanded=False):
                        st.json(tc.get("args", {}))

                for tr in round_rec.get("tool_results", []):
                    with st.expander(f"Tool result: `{tr['tool']}`", expanded=False):
                        result_val = tr.get("result", {})
                        if isinstance(result_val, (dict, list)):
                            st.json(result_val)
                        else:
                            st.text(str(result_val))

            assistant_text = result.get("assistant_text", "")
            if assistant_text:
                st.markdown(assistant_text)

            turn_record: dict[str, Any] = {
                "user": user_input,
                "assistant_text": assistant_text,
                "status": result.get("status", "answered"),
                "rounds": result.get("rounds", []),
                "tool_events": result.get("tool_events", []),
            }

        except Exception as exc:
            status_area.empty()
            error_msg = f"{type(exc).__name__}: {exc}"
            st.error(error_msg)
            turn_record = {
                "user": user_input,
                "assistant_text": f"Error: {error_msg}",
                "status": "provider_error",
                "rounds": [],
                "tool_events": [],
            }

        st.session_state.history.append(turn_record)
