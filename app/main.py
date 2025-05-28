# KnowBot Refactored: Multi-Zone Layout with Saved, Reference, and Search Result Zones

import re

import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from graph import create_graph
from vectorDB import update_db, vector_search
from prompt import SUMMARY_PROMPT, REFERENCE_PROMPT
from utils import format_docs_for_prompt
import concurrent.futures
from config import settings

##############################################
# Functions
##############################################

# --- Session State ---
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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def submit_query():
    if st.session_state.user_input.strip():
        st.session_state.query = st.session_state.user_input.strip()
        st.session_state.submitted = True
        st.session_state.user_input = ""


def summarize_single_doc(doc):
    if not doc.get("content"):
        return "No content to summarize."
    messages = [
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=doc["content"]),
    ]
    summary = ""
    for output in graph.stream({"messages": messages}, config={"streaming": True}):
        msgs = output.get("llm", {}).get("messages") or output.get("messages")
        if msgs and hasattr(msgs[-1], "content"):
            summary += msgs[-1].content
    return summary.strip()

##############################################
# Main
##############################################

init_state()

# Init LangGraph
graph = create_graph()

# --- Streamlit Page Config ---
st.set_page_config(page_title="KnowBot", page_icon="🤖", layout="wide")
st.title("🤖 KnowBot")

# --- Sidebar ---
st.sidebar.header("How to use KnowBot")
st.sidebar.markdown(
    """
1. Enter a question below.  
2. Search or add documents to Saved Articles.  
3. Add references from Saved Articles.  
4. Ask questions using selected references.
"""
)
if st.sidebar.button("🔄 Update Vector DB"):
    update_db()
    st.sidebar.success("Database update complete ✅")
    st.session_state.trigger_rerun = True

# --- Layout ---
main_col, preview_col = st.columns([2, 1])

with main_col:
    # --- Input ---
    st.markdown("### 💬 Ask KnowBot")
    input_col, btn_col = st.columns([10, 1])
    with input_col:
        st.text_input(
            "User Input",
            key="user_input",
            placeholder="e.g. What is LLM orchestration?",
            label_visibility="collapsed",
        )
    with btn_col:
        st.button("Send", on_click=submit_query)

    # --- Search ---
    if st.session_state.submitted and st.session_state.query:
        query = st.session_state.query
        st.session_state.submitted = False

        # Get docs if no reference chosen
        if not st.session_state.reference_docs:
            with st.spinner("Searching and analyzing documents..."):
                docs = vector_search(query)
                st.session_state.related_docs = docs
        else:
            docs = st.session_state.reference_docs

        with st.spinner("Generating Answer with Searched Docs..."):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_summaries = {
                    executor.submit(summarize_single_doc, doc): doc for doc in docs
                }

                answer = ""
                formatted_docs = format_docs_for_prompt(st.session_state.related_docs)
                messages = [
                    SystemMessage(content=REFERENCE_PROMPT),
                    HumanMessage(
                        content=f"Reference:\n{formatted_docs}\n\nQuestion: {query}"
                    ),
                ]
                for output in graph.stream(
                    {"messages": messages}, config={"streaming": True}
                ):
                    msgs = output.get("llm", {}).get("messages") or output.get(
                        "messages"
                    )
                    if msgs and hasattr(msgs[-1], "content"):
                        answer += msgs[-1].content
                st.session_state.answer = "\n".join(answer.strip().split("\n"))
                citations = set(
                    int(match)
                    for match in re.findall(r"\[(\d+)\]", st.session_state.answer)
                )

                for future in concurrent.futures.as_completed(future_summaries):
                    doc = future_summaries[future]
                    try:
                        doc["summary"] = future.result()
                    except Exception as e:
                        doc["summary"] = f"Failed to summarize: {e}"

                st.session_state.related_docs = [
                    doc
                    for i, doc in enumerate(st.session_state.related_docs)
                    if (i + 1) in citations
                ]

    with st.expander("📚 Reference Documents", expanded=True):
        if st.session_state.reference_docs:
            for idx, doc in enumerate(st.session_state.reference_docs):
                row = st.columns([9, 1])
                with row[0]:
                    if st.button(doc["title"], key=f"preview_ref_{idx}"):
                        st.session_state.selected_doc_idx = idx
                        st.session_state.trigger_rerun = True
                with row[1]:
                    if st.button("❌", key=f"remove_ref_{idx}"):
                        st.session_state.reference_docs.pop(idx)
                        st.session_state.trigger_rerun = True
        else:
            st.info("No reference documents selected.")

    with st.expander("📁 Saved Articles", expanded=True):
        if st.session_state.saved_docs:
            for idx, doc in enumerate(st.session_state.saved_docs):
                row = st.columns([1, 9, 1, 1])
                with row[0]:
                    if st.button("📁", key=f"add_ref_from_saved_{idx}"):
                        if doc not in st.session_state.reference_docs:
                            st.session_state.reference_docs.append(doc)
                            st.session_state.trigger_rerun = True
                with row[1]:
                    st.markdown(doc.get("title", "No Title"))
                with row[2]:
                    if st.button("🔍", key=f"view_full_saved_{idx}"):
                        st.session_state.selected_doc_idx = (
                            len(st.session_state.reference_docs) + idx
                        )
                        st.session_state.trigger_rerun = True
                with row[3]:
                    if st.button("❌", key=f"remove_saved_{idx}"):
                        st.session_state.saved_docs.pop(idx)
                        st.session_state.trigger_rerun = True
        else:
            st.info("No saved articles.")

    if st.session_state.answer:
        st.markdown("### ✅ Answer")
        st.write(st.session_state.answer)

    if st.session_state.related_docs:
        st.markdown("### 🔍 Source")
        for idx, doc in enumerate(st.session_state.related_docs):
            row = st.columns([1, 10, 1])
            with row[0]:
                if st.button("📁", key=f"add_saved_{idx}"):
                    if doc not in st.session_state.saved_docs:
                        st.session_state.saved_docs.append(doc)
                        st.session_state.trigger_rerun = True
            with row[1]:
                with st.expander(
                    f"{idx+1}. {doc.get('title', 'No Title')}", expanded=False
                ):
                    st.write("**Summary:**")
                    st.write(doc.get("summary", "No summary"))
                    if st.button("🔍 View Full", key=f"view_full_related_{idx}"):
                        st.session_state.selected_doc_idx = idx
                        st.session_state.trigger_rerun = True
            with row[2]:
                if st.button("➕", key=f"add_ref_direct_{idx}"):
                    if doc not in st.session_state.reference_docs:
                        st.session_state.reference_docs.append(doc)
                        st.session_state.trigger_rerun = True

# --- Preview Pane ---
st.markdown(
    """
    <style>
    .markdown-box {
        height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #fff;
        white-space: pre-wrap;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with preview_col:
    st.markdown("### 📖 Document Preview")

    idx = st.session_state.selected_doc_idx
    all_docs = (
        st.session_state.reference_docs
        + st.session_state.saved_docs
        + st.session_state.related_docs
    )
    if idx is not None and 0 <= idx < len(all_docs):
        doc = all_docs[idx]
        btn_row = st.columns([3, 3, 3])
        with btn_row[0]:
            if st.button("➕ Reference"):
                if doc not in st.session_state.reference_docs:
                    st.session_state.reference_docs.append(doc)
                    st.success("Added to Reference Docs")
                    st.session_state.trigger_rerun = True
                else:
                    st.warning("Already in Reference Docs")
        with btn_row[1]:
            if st.button("💾 Save"):
                if doc not in st.session_state.saved_docs:
                    st.session_state.saved_docs.append(doc)
                    st.success("Saved to Articles")
                    st.session_state.trigger_rerun = True
                else:
                    st.warning("Already Saved")
        with btn_row[2]:
            if st.button("🔙 Back"):
                st.session_state.selected_doc_idx = None
                st.session_state.trigger_rerun = True

        content_html = doc.get("content", "No content.").replace("\n", "<br>")
        st.markdown(
            f'<div class="markdown-box">{content_html}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("Click a document to preview full content here.")

# --- Unified Rerun Trigger ---
if st.session_state.get("trigger_rerun", False):
    st.session_state.trigger_rerun = False
    st.rerun()
