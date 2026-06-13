"""
PyMentor Test UI  –  test_ui.py
================================
A single-file Streamlit app for evaluating PyMentor with real students.

Run:
    streamlit run test_ui.py

Public link (option A – ngrok):
    ngrok http 8501        # in a second terminal

Public link (option B – Streamlit share tunnel):
    streamlit run test_ui.py --server.enableCORS false --server.enableXsrfProtection false

Admin password is set via env var ADMIN_PASSWORD (default: "pymentor_dev").
"""

from __future__ import annotations

import os
import sqlite3
import sys
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="PyMentor – Student Test",
    page_icon="🐍",
    layout="wide",
)

# ── ensure src/ is on the path so python_tutor is importable ──────────────────
_src = Path(__file__).parent / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

# ── import backend ─────────────────────────────────────────────────────────────
IMPORT_ERROR = ""
try:
    from python_tutor import TutorService
    from python_tutor.config import Settings
    from python_tutor.memory import TutorMemory
    BACKEND_OK = True
except ImportError as _e:
    BACKEND_OK = False
    IMPORT_ERROR = str(_e)
    Settings = None  # type: ignore
    TutorMemory = None  # type: ignore
    TutorService = None  # type: ignore

# ── constants ──────────────────────────────────────────────────────────────────
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "pymentor_dev")
DB_PATH = Path(os.getenv("TUTOR_DB_PATH", "data/tutor_memory.db"))

# ── cached singletons ──────────────────────────────────────────────────────────
@st.cache_resource
def get_service() -> "TutorService":
    return TutorService()

@st.cache_resource
def get_memory() -> "TutorMemory":
    if not BACKEND_OK:
        return None  # type: ignore
    settings = Settings()
    return TutorMemory(settings.db_path)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _init_session_state() -> None:
    """Ensure all required session-state keys exist."""
    defaults = {
        "student_name": "",
        "session_id": "",
        "messages": [],           # list[dict] with keys role/content/meta
        "last_result_meta": {},   # debug info from last ask()
        "quiz_active": False,
        "admin_unlocked": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _student_id(name: str) -> str:
    """Convert a display name to a safe student_id key."""
    return name.strip().lower().replace(" ", "_")


def _get_profile(student_id: str) -> dict:
    mem = get_memory()
    if mem is None:
        return {"ability": "unknown", "mastered_topics": [], "struggling_topics": [], "misconceptions": []}
    return mem.profile(student_id)


def _has_pending_quiz(student_id: str, session_id: str) -> dict | None:
    mem = get_memory()
    if mem is None:
        return None
    return mem.get_pending_quiz(student_id, session_id)


def _reset_student(student_id: str) -> None:
    """Delete all memory rows for this student (admin action)."""
    db_path = Settings().db_path  # type: ignore[misc]
    con = sqlite3.connect(db_path)
    try:
        for table in ("students", "messages", "quiz_attempts", "misconceptions", "quiz_state"):
            con.execute(f"DELETE FROM {table} WHERE student_id = ?", (student_id,))
        con.commit()
    finally:
        con.close()


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR – student identity + profile panel + admin
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar() -> None:
    with st.sidebar:
        st.title("🐍 PyMentor")

        # ── student name ───────────────────────────────────────────────────
        st.subheader("Who are you?")
        name_input = st.text_input(
            "Your first name (or nickname)",
            value=st.session_state.student_name,
            placeholder="e.g. Alex",
            key="name_field",
        )

        if st.button("▶  Start / Switch student", use_container_width=True):
            if name_input.strip():
                st.session_state.student_name = name_input.strip()
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.messages = []
                st.session_state.quiz_active = False
                st.session_state.last_result_meta = {}
                st.rerun()
            else:
                st.warning("Please enter a name first.")

        if st.session_state.student_name:
            st.caption(f"Session: `{st.session_state.session_id[:8]}…`")
            st.divider()

            # ── profile panel ──────────────────────────────────────────────
            sid = _student_id(st.session_state.student_name)
            profile = _get_profile(sid)

            with st.expander("📊 Your learning profile", expanded=True):
                ability_color = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}.get(
                    profile["ability"], "⚪"
                )
                st.markdown(f"**Level:** {ability_color} {profile['ability'].capitalize()}")

                mastered = profile.get("mastered_topics") or []
                st.markdown(
                    "**Mastered:** " + (", ".join(f"`{t}`" for t in mastered) if mastered else "_none yet_")
                )

                struggling = profile.get("struggling_topics") or []
                st.markdown(
                    "**Struggling:** " + (", ".join(f"`{t}`" for t in struggling) if struggling else "_none yet_")
                )

                misconceptions = profile.get("misconceptions") or []
                if misconceptions:
                    st.markdown("**Recent misconceptions:**")
                    for m in misconceptions[:5]:
                        st.markdown(
                            f"- `{m['topic']}` – {m['misconception']} "
                            f"*(×{m['occurrences']})*"
                        )
                else:
                    st.markdown("**Misconceptions:** _none recorded_")

            # ── pending quiz banner ────────────────────────────────────────
            pending = _has_pending_quiz(sid, st.session_state.session_id)
            if pending:
                st.warning(
                    f"⏳ **Quiz pending** on `{pending['topic']}`  \n"
                    "Please answer the quiz question before asking something new."
                )

        st.divider()

        # ── admin panel ────────────────────────────────────────────────────
        with st.expander("🔒 Admin / Debug", expanded=False):
            if not st.session_state.admin_unlocked:
                pw = st.text_input("Password", type="password", key="admin_pw")
                if st.button("Unlock"):
                    if pw == ADMIN_PASSWORD:
                        st.session_state.admin_unlocked = True
                        st.rerun()
                    else:
                        st.error("Wrong password.")
            else:
                st.success("Admin mode active")
                _render_admin_panel()


def _render_admin_panel() -> None:
    meta = st.session_state.last_result_meta

    if meta:
        st.markdown("**Last intent:**  `" + str(meta.get("intent", "—")) + "`")
        conf = meta.get("confidence", None)
        if conf is not None:
            st.markdown(f"**Retrieval confidence:** `{conf:.2f}`")
        ctx_ok = meta.get("context_sufficient")
        if ctx_ok is not None:
            st.markdown("**Context sufficient:** " + ("✅ yes" if ctx_ok else "❌ no"))
        guards = meta.get("guardrails_triggered") or []
        if guards:
            st.markdown("**Guardrails triggered:** " + ", ".join(f"`{g}`" for g in guards))
        next_act = meta.get("next_action", "")
        if next_act:
            st.markdown(f"**Next action:** `{next_act}`")

        sources = meta.get("sources") or []
        if sources:
            with st.expander("Retrieved sources"):
                for s in sources:
                    st.write(f"`{s.get('source_id','')}` {s.get('section','')} score={s.get('score',0):.2f}")
    else:
        st.caption("No request made yet in this session.")

    st.divider()

    # ── reset student ──────────────────────────────────────────────────────
    if st.session_state.student_name:
        sid = _student_id(st.session_state.student_name)
        st.markdown(f"**Reset student:** `{sid}`")
        if st.button("🗑️  Delete all memory for this student", type="primary"):
            _reset_student(sid)
            st.session_state.messages = []
            st.session_state.quiz_active = False
            st.session_state.last_result_meta = {}
            st.success(f"Memory cleared for {sid}.")
            st.rerun()

    # ── reset any student by name ──────────────────────────────────────────
    st.divider()
    other = st.text_input("Reset a different student ID", key="admin_reset_other")
    if st.button("🗑️  Reset other student"):
        if other.strip():
            _reset_student(_student_id(other.strip()))
            st.success(f"Cleared: {_student_id(other.strip())}")
        else:
            st.warning("Enter a student name first.")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN CHAT AREA
# ══════════════════════════════════════════════════════════════════════════════

def render_chat() -> None:
    if not st.session_state.student_name:
        st.info("👈 Enter your name in the sidebar and click **Start** to begin.")
        return

    if not BACKEND_OK:
        st.error(f"Backend import failed: {IMPORT_ERROR}")
        st.stop()

    student_name = st.session_state.student_name
    sid = _student_id(student_name)
    session_id = st.session_state.session_id

    # ── pending quiz top banner ────────────────────────────────────────────
    pending = _has_pending_quiz(sid, session_id)
    if pending:
        st.info(
            f"🧪 **Quiz active** – Topic: `{pending['topic']}`  \n"
            "Type your answer below. The tutor is waiting for your response."
        )

    st.markdown(f"### Chat – *{student_name}*")

    # ── render message history ─────────────────────────────────────────────
    for msg in st.session_state.messages:
        role = msg["role"]
        with st.chat_message(role):
            if role == "assistant" and msg.get("is_quiz"):
                # Quiz question styling
                st.markdown(
                    f"<div style='border-left:4px solid #f39c12; padding-left:10px'>"
                    f"{msg['content']}</div>",
                    unsafe_allow_html=True,
                )
                st.caption("🧪 Quiz question – answer in the chat box below")
            else:
                st.markdown(msg["content"])

            # Show grading result if present
            if msg.get("grading"):
                grade = msg["grading"]
                if grade.get("correct"):
                    st.success("✅ Correct!")
                else:
                    st.error("❌ Incorrect – see the tutor's feedback above.")

            # Show guardrails in message
            if msg.get("guardrails"):
                st.caption("🛡️ Guardrails: " + ", ".join(msg["guardrails"]))

    # ── chat input ─────────────────────────────────────────────────────────
    placeholder = (
        "Type your answer to the quiz…" if pending
        else "Ask about Python, request a quiz, or ask for your progress…"
    )

    user_input = st.chat_input(placeholder)

    if user_input:
        _handle_message(user_input, sid, session_id)
        st.rerun()


def _handle_message(user_input: str, student_id: str, session_id: str) -> None:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    service = get_service()
    try:
        result = service.ask(
            student_id=student_id,
            session_id=session_id,
            message=user_input,
        )
    except Exception as exc:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"⚠️ Error: {exc}",
        })
        return

    # Determine if this is a quiz question from the tutor
    intent = result.intent or ""
    is_quiz_question = intent in ("quiz",) or "quiz" in result.next_action.lower()

    # Detect grading result: the tutor returns quiz_answer intent when grading
    is_grading = intent == "quiz_answer" or "correct" in result.response.lower()[:80]
    grading_result = None
    if is_grading:
        correct_signal = any(
            w in result.response.lower()[:120]
            for w in ("correct", "well done", "great", "right", "exactly", "perfect")
        )
        grading_result = {"correct": correct_signal}

    # Store debug meta
    st.session_state.last_result_meta = {
        "intent": result.intent,
        "confidence": result.confidence,
        "guardrails_triggered": result.guardrails_triggered,
        "next_action": result.next_action,
        "sources": [s.model_dump() for s in result.sources],
    }

    assistant_msg: dict = {
        "role": "assistant",
        "content": result.response,
        "is_quiz": is_quiz_question,
        "guardrails": result.guardrails_triggered or [],
        "grading": grading_result,
    }
    st.session_state.messages.append(assistant_msg)
    st.session_state.quiz_active = is_quiz_question


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    _init_session_state()
    render_sidebar()
    render_chat()


main()
