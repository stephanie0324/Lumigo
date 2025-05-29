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

def extract_used_doc_indices(answer):
    # 抓取所有形如 [1], [2], 等的引用，並去掉重複與轉成 index（-1）
    matches = re.findall(r"\[(\d+)\]", answer)
    indices = {int(m) - 1 for m in matches if m.isdigit()}
    return indices

##############################################
# Main
##############################################

init_state()

# Init LangGraph
graph = create_graph()

# --- Streamlit Page Config ---
st.set_page_config(page_title=settings.DEMO_WEB_PAGE_TITLE, page_icon="🤖", layout="wide")
st.title(settings.DEMO_WEB_PAGE_TITLE)

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

                # 確保每篇都有 title
                for i, doc in enumerate(docs):
                    doc["title"] = doc.get("title") or f"Untitled {i+1}"

                st.session_state.related_docs = docs
        else:
            docs = st.session_state.reference_docs

        # 預先摘要處理
        with st.spinner("Summarizing documents..."):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_summaries = {
                    executor.submit(summarize_single_doc, doc): doc for doc in docs
                }
                for future in concurrent.futures.as_completed(future_summaries):
                    doc = future_summaries[future]
                    try:
                        doc["summary"] = future.result()
                    except Exception as e:
                        doc["summary"] = f"Failed to summarize: {e}"

        # 生成回答
        with st.spinner("Generating Answer with Documents..."):
            formatted_docs = format_docs_for_prompt(st.session_state.related_docs)
            messages = [
                SystemMessage(content=REFERENCE_PROMPT),
                HumanMessage(
                    content=f"Reference:\n{formatted_docs}\n\nQuestion: {query}"
                ),
            ]
            answer = ""
            for output in graph.stream(
                {"messages": messages}, config={"streaming": True}
            ):
                msgs = output.get("llm", {}).get("messages") or output.get("messages")
                if msgs and hasattr(msgs[-1], "content"):
                    answer += msgs[-1].content

            st.session_state.answer = "\n".join(answer.strip().split("\n"))
    used_indices = extract_used_doc_indices(st.session_state.answer)
    st.markdown(st.session_state.answer or "No answer generated yet.")


with preview_col:
    st.markdown("### 📄 Docs")

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
            
    if st.session_state.related_docs:
        st.markdown("### 🔍 Source")
        for idx in used_indices:
            doc = st.session_state.related_docs[idx]
            row = st.columns([1, 1, 10])
            with row[0]:
                if st.button("➕", key=f"add_ref_direct_{idx}"):
                    if doc not in st.session_state.reference_docs:
                        st.session_state.reference_docs.append(doc)
                        st.session_state.trigger_rerun = True
            with row[2]:
                with st.expander(
                    f"{idx+1}. {doc.get('title', 'No Title')}", expanded=False
                ):
                    st.write("**Summary:**")
                    st.write(doc.get("summary", "No summary"))

# --- Unified Rerun Trigger ---
if st.session_state.get("trigger_rerun", False):
    st.session_state.trigger_rerun = False
    st.rerun()
