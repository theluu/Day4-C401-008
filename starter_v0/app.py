from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version, artifact_version_dict
from chat import run_model_tool_loop, write_transcript

load_lab_env(ROOT)

ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
PROVIDERS = ["openai", "openrouter", "anthropic", "gemini"]


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@st.dialog("📧 Gửi câu trả lời qua Email")
def _email_dialog(content: str, question: str, email_to: str, sent_key: str) -> None:
    st.write(f"Gửi tới: **{email_to}**")
    st.write(f"Tiêu đề: **Research Agent: {question[:60]}**")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Xác nhận gửi", type="primary", use_container_width=True):
            with st.spinner("Đang gửi email..."):
                from tools.email.tool import send_email
                result = send_email(
                    to=email_to,
                    subject=f"Research Agent: {question[:60]}",
                    body=content,
                    confirmed=True,
                )
            if result.get("status") in ("sent", "simulated"):
                st.session_state[sent_key] = "sent"
                st.toast(f"✅ Đã gửi tới {email_to}", icon="✅")
            else:
                st.session_state[sent_key] = f"err:{result.get('message','')}"
            st.rerun()
    with c2:
        if st.button("❌ Huỷ", use_container_width=True):
            st.rerun()


def _send_answer_email(content: str, question: str, btn_key: str) -> None:
    email_to = os.getenv("EMAIL_USER", "")
    if not email_to:
        st.warning("Chưa set EMAIL_USER trong .env")
        return

    sent_key = f"_email_sent_{btn_key}"
    state = st.session_state.get(sent_key)

    if state == "sent":
        st.success(f"✅ Đã gửi tới {email_to}")
        if st.button("Gửi lại", key=f"{btn_key}_again"):
            st.session_state.pop(sent_key, None)
            _email_dialog(content, question, email_to, sent_key)
        return

    if state and state.startswith("err:"):
        st.error(f"❌ Lỗi: {state[4:]}")

    if st.button("📧 Gửi qua Email", key=btn_key):
        _email_dialog(content, question, email_to, sent_key)


def _render_tool_expander(tool_events: list[dict]) -> None:
    n = len(tool_events)
    label = f"🔧 Tool calls ({n})"
    with st.expander(label):
        for event in tool_events:
            tool_name = event.get("tool", "unknown")
            args = event.get("args", {})
            result = event.get("result", {})
            st.markdown(f"**`{tool_name}`**")
            col1, col2 = st.columns(2)
            with col1:
                st.caption("Args")
                st.json(args)
            with col2:
                st.caption("Result")
                st.json(result)
            st.divider()


RUNS_DIR = ROOT / "runs"


def _load_run(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _render_eval_tab() -> None:
    # ── Run Eval controls ─────────────────────────────────────────────────────
    with st.expander("🚀 Run Eval", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            run_provider = st.selectbox("Provider", PROVIDERS, key="eval_provider")
        with col2:
            run_version = st.text_input("Version", value="v0", key="eval_version")
        with col3:
            suite_options = {"base": "data/eval_base.json", "group": "data/eval_group.json", "extension": "data/eval_research_extension.json"}
            run_suite = st.selectbox("Suite", list(suite_options.keys()), key="eval_suite")

        if st.button("▶ Run Eval", type="primary", use_container_width=True):
            eval_cases = suite_options[run_suite]
            cmd = [
                sys.executable, "run_eval.py",
                "--provider", run_provider,
                "--version", run_version,
                "--suite", run_suite,
                "--eval-cases", eval_cases,
            ]
            output_box = st.empty()
            output_lines: list[str] = []
            with st.spinner(f"Running {run_suite} eval v{run_version}..."):
                proc = subprocess.Popen(
                    cmd, cwd=str(ROOT),
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                )
                for line in proc.stdout:
                    output_lines.append(line.rstrip())
                    output_box.code("\n".join(output_lines[-30:]))
                proc.wait()
            if proc.returncode == 0:
                st.success("Eval hoàn thành! Chọn run file mới bên dưới để xem kết quả.")
                st.rerun()
            else:
                st.error("Eval thất bại. Xem log ở trên.")

    st.divider()

    # ── Run file selector ─────────────────────────────────────────────────────
    run_files = sorted(RUNS_DIR.glob("*.json"), reverse=True)
    if not run_files:
        st.info("Chưa có run JSON nào trong thư mục `runs/`. Nhấn 'Run Eval' ở trên.")
        return

    names = [f.name for f in run_files]
    # Default to latest baseline (v0_B_base) if available
    default_idx = next((i for i, n in enumerate(names) if "v0_B_base" in n), 0)
    selected = st.selectbox("Chọn run file", names, index=default_idx)
    run = _load_run(RUNS_DIR / selected)

    summary = run.get("summary", {})
    st.caption(f"Version: **{run.get('version')}** · Suite: **{run.get('suite')}** · Provider: **{run.get('provider')}** · {run.get('generated_at', '')}")
    st.divider()

    # ── Metrics ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cases", f"{summary.get('passed_cases', 0)}/{summary.get('total_cases', 0)}")
    c2.metric("Case Accuracy", f"{summary.get('case_accuracy', 0):.0%}")
    c3.metric("Tool Routing", f"{summary.get('tool_routing_accuracy', 0):.0%}")
    c4.metric("Arg Accuracy", f"{summary.get('argument_accuracy', 0):.0%}")
    mt = summary.get("multiturn_accuracy")
    c5.metric("Multi-turn", f"{mt:.0%}" if mt is not None else "N/A")

    st.divider()

    # ── Per-case table ────────────────────────────────────────────────────────
    st.subheader("Kết quả từng case")
    for item in run.get("results", []):
        r = item["result"]
        passed = r.get("passed", False)
        icon = "✅" if passed else "❌"
        label = f"{icon} `{item['id']}`"
        if r.get("failures"):
            label += f" — {', '.join(r['failures'][:2])}"
        with st.expander(label, expanded=not passed):
            col1, col2 = st.columns(2)
            with col1:
                st.caption("Expected tool calls")
                st.json(item.get("expect", {}).get("tool_calls") or "no_tool")
            with col2:
                st.caption("Actual tool calls")
                st.json(r.get("actual_tool_calls", []))
            if r.get("observed_mismatch"):
                st.warning(f"Mismatch: {r['observed_mismatch']}")


st.set_page_config(page_title="Research Agent", page_icon="🔍", layout="wide")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 Research Agent")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0)
    version_label = st.text_input("Version", value="v0")
    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ── Session state init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "transcript" not in st.session_state:
    ts = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    st.session_state.transcript_id = f"{version_label}_{provider_name}_{ts}"
    st.session_state.transcript = {
        "transcript_id": st.session_state.transcript_id,
        "provider": provider_name,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{st.session_state.transcript_id}.transcript.json"

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_chat, tab_eval = st.tabs(["💬 Chat", "📊 Eval Results"])

with tab_eval:
    _render_eval_tab()

with tab_chat:
    # ── Render existing messages ──────────────────────────────────────────────
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tool_events"):
                _render_tool_expander(msg["tool_events"])
            if msg["role"] == "assistant":
                prev = st.session_state.messages[i - 1] if i > 0 else {}
                _send_answer_email(msg["content"], prev.get("content", ""), f"email_hist_{i}")

    # ── Handle new user input ─────────────────────────────────────────────────
    user_text = st.chat_input("Nhập câu hỏi...")
    if user_text:
        with st.chat_message("user"):
            st.markdown(user_text)
        st.session_state.messages.append({"role": "user", "content": user_text, "tool_events": []})
        st.session_state.history.append({"role": "user", "content": user_text})

        system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
        tool_declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
        openai_tools = to_openai_tools(tool_declarations)

        try:
            provider = make_provider(provider_name)
        except Exception as exc:
            st.error(f"Provider error: {exc}. Check your .env API key for '{provider_name}'.")
            st.stop()

        messages_for_model = [
            {"role": "system", "content": system_prompt},
            *st.session_state.history[:-1],
            {"role": "user", "content": user_text},
        ]

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = run_model_tool_loop(
                        provider=provider,
                        messages=messages_for_model,
                        tools=openai_tools,
                        model=None,
                        max_tool_rounds=4,
                    )
                except Exception as exc:
                    st.error(f"Agent error: {exc}")
                    st.stop()

            assistant_text = result["assistant_text"]
            tool_events = result.get("tool_events", [])

            st.markdown(assistant_text)
            if tool_events:
                _render_tool_expander(tool_events)
            _send_answer_email(assistant_text, user_text, "email_new")

        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_text,
            "tool_events": tool_events,
        })
        st.session_state.history.append({"role": "assistant", "content": assistant_text})

        turn = {
            "turn_index": len(st.session_state.transcript["turns"]) + 1,
            "user": user_text,
            "assistant_text": assistant_text,
            "tool_events": tool_events,
            "status": result.get("status", "answered"),
        }
        st.session_state.transcript["turns"].append(turn)
        write_transcript(st.session_state.transcript_path, st.session_state.transcript)
