# KnowBot Refactored: Multi-Zone Layout

import re
import asyncio
import concurrent.futures
import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from graph import create_graph
from vectorDB import update_db_async, vector_search
from prompt import SUMMARY_PROMPT, REFERENCE_PROMPT
from utils import format_docs_for_prompt
from config import settings
from logger import logger

# -----------------------------
# Session Initialization
# -----------------------------
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# -----------------------------
# Logic Functions
# -----------------------------
def submit_query():
    if st.session_state.user_input.strip():
        st.session_state.query = st.session_state.user_input.strip()
        st.session_state.submitted = True

def trigger_question(question):
    st.session_state.user_input = question
    st.session_state.query = question
    st.session_state.submitted = True   # <== 加上這行
    st.session_state.trigger_rerun = True


def summarize_single_doc(doc):
    if not doc.get("content"):
        return "No content to summarize."
    messages = [SystemMessage(content=SUMMARY_PROMPT), HumanMessage(content=doc["content"])]
    summary = ""
    for output in graph.stream({"messages": messages}, config={"streaming": True}):
        msgs = output.get("llm", {}).get("messages") or output.get("messages")
        if msgs and hasattr(msgs[-1], "content"):
            summary += msgs[-1].content
    return summary.strip()

def extract_used_doc_indices(answer):
    return {int(m) - 1 for m in re.findall(r"\[(\d+)\]", answer)}

def split_answer_followups(raw_answer):
    parts = re.split(r"\n^#{1,6}\s*💡.*$", raw_answer, flags=re.MULTILINE)
    return (parts[0].strip(), parts[1].strip() if len(parts) > 1 else "")

def extract_followups(response: str):
    return re.findall(r"> #### (.+)", response)

# -----------------------------
# Main App Logic
# -----------------------------
init_state()
graph = create_graph()
st.set_page_config(page_title=settings.DEMO_WEB_PAGE_TITLE, page_icon="🤖", layout="wide")
st.title(settings.DEMO_WEB_PAGE_TITLE)

# --- Sidebar ---
st.sidebar.header("How to use KnowBot")
st.sidebar.markdown("""
1. Enter a question below.  
2. Search or add documents to Saved Articles.  
3. Add references from Saved Articles.  
4. Ask questions using selected references.
""")

if st.sidebar.button("🔄 Update Vector DB"):
    with st.sidebar:
        with st.spinner("Updating database..."):
            asyncio.run(update_db_async())
        st.success("Database update complete ✅")
        st.session_state.trigger_rerun = True

# --- Main Layout ---
main_col, preview_col = st.columns([2, 1])

# ===============================
# Main Column: Input & Answer
# ===============================
with main_col:
    st.markdown("### 💬 Ask KnowBot")
    input_col, btn_col = st.columns([10, 1])
    input_col.text_input(
        "User Input", key="user_input",
        value=st.session_state.user_input,
        placeholder="e.g. What is LLM orchestration?",
        label_visibility="collapsed",
    )
    if btn_col.button("Send"):
        submit_query()

    if st.session_state.submitted and st.session_state.query:
        query = st.session_state.query
        st.session_state.submitted = False

        # Get related docs only if no reference selected
        if not st.session_state.reference_docs:
            with st.spinner("Searching and analyzing documents..."):
                docs = vector_search(query)
                for i, doc in enumerate(docs):
                    doc["title"] = doc.get("title") or f"Untitled {i+1}"
                st.session_state.related_docs = docs
        else:
            docs = st.session_state.reference_docs

        # Generate answer
        with st.spinner("Generating Answer with Documents..."):
            formatted = format_docs_for_prompt(st.session_state.related_docs)
            messages = [
                SystemMessage(content=REFERENCE_PROMPT),
                HumanMessage(content=f"Reference:\n{formatted}\n\nQuestion: {query}")
            ]
            answer = ""
            for output in graph.stream({"messages": messages}, config={"streaming": True}):
                msgs = output.get("llm", {}).get("messages") or output.get("messages")
                if msgs and hasattr(msgs[-1], "content"):
                    answer += msgs[-1].content

            raw_answer = "\n".join(answer.strip().split("\n"))
            trimmed, followup = split_answer_followups(raw_answer)
            st.session_state.answer = trimmed
            st.session_state.used_indices = list(extract_used_doc_indices(trimmed))
            followups = extract_followups(followup)

            st.markdown("#### 🤖 Answer")
            st.markdown(trimmed)

            st.markdown("### 💡 Explore Further")
            for i, q in enumerate(followups):
                st.button(
                    q,
                    key=f"followup_{i}",
                    on_click=trigger_question,
                    args=(q,)
                )

# ===============================
# Preview Column: Docs Management
# ===============================
with preview_col:
    st.markdown("### 📄 Docs")

    with st.expander("📚 Reference Documents", expanded=True):
        if st.session_state.reference_docs:
            for idx, doc in enumerate(st.session_state.reference_docs):
                row = st.columns([9, 1])
                with row[0]:
                    if st.button(doc["title"], key=f"ref_doc_{idx}"):
                        st.session_state.selected_doc_idx = idx
                with row[1]:
                    if st.button("❌", key=f"remove_ref_{idx}"):
                        st.session_state.reference_docs.pop(idx)
                        st.session_state.trigger_rerun = True
        else:
            st.info("No reference documents selected.")

    if st.session_state.related_docs:
        st.markdown("### 🔍 Source")
        for idx in st.session_state.used_indices:
            doc = st.session_state.related_docs[idx]
            row = st.columns([1, 1, 10])
            with row[0]:
                if st.button("➕", key=f"add_ref_{idx}"):
                    if doc not in st.session_state.reference_docs:
                        st.session_state.reference_docs.append(doc)
                        st.session_state.trigger_rerun = True
            with row[2]:
                with st.expander(f" [{idx+1}]  {doc.get('title', 'No Title')}"):
                    st.write("**Summary:**")
                    content = doc.get("content", "")
                    preview = content[:500] + "..." if len(content) > 500 else content
                    st.write(preview)

