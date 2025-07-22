import re
import streamlit as st
from core.multi_graph import create_graph
from core.build_faiss_index import run_indexing_pipeline

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


def trigger_build_index():
    """Wrapper to run the FAISS index building pipeline and show progress in Streamlit."""
    with st.spinner("Building FAISS index from source documents... Please wait."):
        run_indexing_pipeline()
    st.success("✅ FAISS index has been successfully built!")
