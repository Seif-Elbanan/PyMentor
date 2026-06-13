from __future__ import annotations

import uuid

import streamlit as st
from dotenv import load_dotenv

from python_tutor import TutorService


load_dotenv()
st.set_page_config(page_title="PyMentor", page_icon="P", layout="wide")


@st.cache_resource
def get_service() -> TutorService:
    return TutorService()


st.title("PyMentor")
st.caption("A memory-aware, grounded Python tutor built with LangGraph")

with st.sidebar:
    st.header("Learner")
    student_id = st.text_input("Student ID", value="demo-student")
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if st.button("New session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    st.write("Session:", st.session_state.session_id[:8])
    st.info("The tutor gives hints instead of complete homework solutions.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Grounding sources"):
                for source in message["sources"]:
                    st.write(
                        f"`{source['source_id']}` - {source['section']} "
                        f"(score {source['score']:.2f})"
                    )

prompt = st.chat_input("Ask about Python or request a quiz")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking through the learning path..."):
            try:
                result = get_service().ask(
                    student_id=student_id,
                    session_id=st.session_state.session_id,
                    message=prompt,
                )
                st.markdown(result.response)
                if result.sources:
                    with st.expander("Grounding sources"):
                        for source in result.sources:
                            st.write(
                                f"`{source.source_id}` - {source.section} "
                                f"(score {source.score:.2f})"
                            )
                if result.guardrails_triggered:
                    st.caption("Guardrails: " + ", ".join(result.guardrails_triggered))
                st.caption(f"Next: {result.next_action}")
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": result.response,
                        "sources": [source.model_dump() for source in result.sources],
                    }
                )
            except Exception as exc:
                st.error(f"Tutor error: {exc}")
