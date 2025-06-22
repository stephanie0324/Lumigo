import re
import streamlit as st
from core.multi_graph import create_graph
from utils.db_utils import update_db_async


def init_state():
    defaults = {
        "saved_docs": [],
        "reference_docs": [],
        "related_docs": [],
        "query": "",
        "submitted": False,
        "selected_doc_idx": None,
        "answer": "",
        "user_input": "",
        "markdown_doc": "",
        "trigger_rerun": False,
        "used_indices": [],
        "explore_mode": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def submit_query():
    if st.session_state.user_input.strip():
        st.session_state.query = st.session_state.user_input.strip()
        st.session_state.submitted = True


def trigger_question(question):
    st.session_state.user_input = question
    st.session_state.query = question
    st.session_state.submitted = True
    st.session_state.trigger_rerun = True


def extract_used_doc_indices(answer):
    return {int(m) - 1 for m in re.findall(r"\[\^(\d+)\]", answer)}


def split_answer_followups(raw_answer):
    parts = re.split(r"\n^#{1,6}\s*💡.*$", raw_answer, flags=re.MULTILINE)
    return (parts[0].strip(), parts[1].strip() if len(parts) > 1 else "")


def extract_followups(response: str):
    return re.findall(r"> #### (.+)", response)


def get_graph():
    return create_graph()


async def async_update_db():
    await update_db_async()
