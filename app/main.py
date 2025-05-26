# KnowBot Refactored: Multi-Zone Layout with Saved, Reference, and Search Result Zones

import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from graph import create_graph
from vectorDB import update_db, vector_search
from prompt import SUMMARY_PROMPT, REFERENCE_PROMPT

# Init LangGraph
graph = create_graph()

# --- Streamlit Page Config ---
st.set_page_config(page_title="KnowBot", page_icon="🤖", layout="wide")
st.title("🤖 KnowBot")

# --- Custom CSS ---
st.markdown(
    """
    <style>
    .scroll-box {
        height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #f9f9f9;
        white-space: pre-wrap;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# --- Utility Functions ---
def submit_query():
    if st.session_state.user_input.strip():
        st.session_state.query = st.session_state.user_input.strip()
        st.session_state.submitted = True
        st.session_state.user_input = ""


def summarize_document(doc_content):
    if not doc_content:
        return "No content to summarize."
    messages = [
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=doc_content),
    ]
    summary = ""
    for output in graph.stream({"messages": messages}, config={"streaming": True}):
        msgs = output.get("llm", {}).get("messages") or output.get("messages")
        if msgs and hasattr(msgs[-1], "content"):
            summary += msgs[-1].content
    return summary.strip()


# --- Layout ---
main_col, preview_col = st.columns([2, 1])

with main_col:
    # --- Input ---
    st.markdown("### 💬 Ask KnowBot")
    input_col, btn_col = st.columns([10, 1])
    with input_col:
        st.text_input(
            "",
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

        with st.spinner("Searching and analyzing documents..."):
            if st.session_state.reference_docs:
                ref_text = "\n\n".join(
                    [doc["content"] for doc in st.session_state.reference_docs]
                )
                messages = [
                    SystemMessage(content=REFERENCE_PROMPT),
                    HumanMessage(
                        content=f"Reference:\n{ref_text}\n\nQuestion: {query}"
                    ),
                ]
                answer = ""
                for output in graph.stream(
                    {"messages": messages}, config={"streaming": True}
                ):
                    msgs = output.get("llm", {}).get("messages") or output.get(
                        "messages"
                    )
                    if msgs and hasattr(msgs[-1], "content"):
                        answer += msgs[-1].content
                st.session_state.answer = "\n".join(answer.strip().split("\n"))
            else:
                docs = vector_search(query)
                for doc in docs:
                    if "summary" not in doc or not doc["summary"]:
                        doc["summary"] = summarize_document(doc.get("content", ""))
                st.session_state.related_docs = docs

    # --- Answer ---
    if st.session_state.answer:
        st.markdown("### ✅ Answer")
        st.write(st.session_state.answer)
        st.download_button(
            "📋 Copy Answer", st.session_state.answer, file_name="answer.txt"
        )

    # --- Search Results ---
    if st.session_state.related_docs:
        st.markdown("### 🔍 Search Results")
        for idx, doc in enumerate(st.session_state.related_docs):
            row = st.columns([1, 10, 1])
            with row[0]:
                if st.button("➕", key=f"add_saved_{idx}"):
                    if doc not in st.session_state.saved_docs:
                        st.session_state.saved_docs.append(doc)
            with row[1]:
                with st.expander(
                    f"{idx+1}. {doc.get('title', 'No Title')}", expanded=False
                ):
                    st.write("**Summary:**")
                    st.write(doc.get("summary", "No summary"))
                    if st.button("🔍 View Full", key=f"view_full_related_{idx}"):
                        st.session_state.selected_doc_idx = idx
            with row[2]:
                if st.button("⭐", key=f"add_ref_direct_{idx}"):
                    if doc not in st.session_state.reference_docs:
                        st.session_state.reference_docs.append(doc)

    # --- Saved Articles ---
    if st.session_state.saved_docs:
        st.markdown("### 📁 Saved Articles")
        for idx, doc in enumerate(st.session_state.saved_docs):
            row = st.columns([1, 9, 1, 1])
            with row[0]:
                if st.button("⭐", key=f"add_ref_from_saved_{idx}"):
                    if doc not in st.session_state.reference_docs:
                        st.session_state.reference_docs.append(doc)
            with row[1]:
                st.markdown(doc.get("title", "No Title"))
            with row[2]:
                if st.button("🔍", key=f"view_full_saved_{idx}"):
                    st.session_state.selected_doc_idx = (
                        len(st.session_state.reference_docs) + idx
                    )
            with row[3]:
                if st.button("❌", key=f"remove_saved_{idx}"):
                    st.session_state.saved_docs.pop(idx)
                    st.experimental_rerun()

    # --- Reference Docs ---
    if st.session_state.reference_docs:
        st.markdown("### 📚 Reference Documents")
        for idx, doc in enumerate(st.session_state.reference_docs):
            row = st.columns([9, 1])
            with row[0]:
                if st.button(doc["title"], key=f"preview_ref_{idx}"):
                    st.session_state.selected_doc_idx = idx
            with row[1]:
                if st.button("❌", key=f"remove_ref_{idx}"):
                    st.session_state.reference_docs.pop(idx)
                    st.experimental_rerun()
    else:
        st.info("No reference documents selected.")

# --- Preview Pane ---
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
        st.markdown(f"**{doc.get('title', 'No Title')}**")
        st.markdown("---")
        html_content = doc.get("content", "No content.").replace("\n", "<br>")
        st.markdown(
            f'<div class="scroll-box">{html_content}</div>', unsafe_allow_html=True
        )
        if st.button("🔙 Back"):
            st.session_state.selected_doc_idx = None
            st.experimental_rerun()
    else:
        st.info("Click a document to preview full content here.")
