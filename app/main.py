import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from graph import create_graph
from vectorDB import update_db, vector_search
from prompt import SUMMARY_PROMPT, REFERENCE_PROMPT

# Init LangGraph
graph = create_graph()

st.set_page_config(page_title="KnowBot", page_icon="🤖", layout="wide")
st.title("🤖 KnowBot")

# --- Custom CSS for scrollable preview box ---
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
2. (Optional) Add reference documents.  
3. KnowBot will answer using selected or most relevant documents.
"""
)
if st.sidebar.button("🔄 Update Vector DB"):
    update_db()
    st.sidebar.success("Database update complete ✅")


# --- Session State Initialization ---
def init_state():
    defaults = {
        "reference_docs": [],
        "related_docs": [],
        "query": "",
        "submitted": False,
        "selected_doc_idx": None,
        "answer": "",
        "user_input": "",
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


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


# --- Main layout ---
main_col, preview_col = st.columns([2, 1])

with main_col:
    # Input Area
    st.markdown("### 💬 Ask KnowBot")
    input_col, btn_col = st.columns([10, 1])
    with input_col:
        st.text_input(
            "",
            key="user_input",
            placeholder="e.g. How does KnowBot work?",
            label_visibility="collapsed",
        )
    with btn_col:
        st.button(
            "Send" if st.session_state.reference_docs else "Search",
            on_click=submit_query,
        )

    # Reference Document List
    st.markdown("#### 📚 Reference Documents")
    if st.session_state.reference_docs:
        for idx, doc in enumerate(st.session_state.reference_docs):
            col1, col2 = st.columns([9, 1])
            with col1:
                if st.button(doc["title"], key=f"preview_ref_{idx}"):
                    st.session_state.selected_doc_idx = idx
            with col2:
                if st.button("❌", key=f"remove_ref_{idx}"):
                    st.session_state.reference_docs.pop(idx)
                    st.experimental_rerun()
    else:
        st.info("No reference documents selected.")

    # --- Query Handling ---
    if st.session_state.submitted and st.session_state.query:
        query = st.session_state.query
        st.session_state.submitted = False

        with st.spinner(
            "Thinking..." if st.session_state.reference_docs else "Searching docs..."
        ):
            if st.session_state.reference_docs:
                docs = st.session_state.reference_docs
                ref_text = "\n\n".join([d.get("content", "") for d in docs])
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

    # --- Answer Output ---
    if st.session_state.answer:
        st.markdown("### ✅ Answer")
        st.write(st.session_state.answer)
        st.download_button(
            "📋 Copy Answer", st.session_state.answer, file_name="answer.txt"
        )

    # --- Related Documents ---
    if st.session_state.related_docs:
        st.markdown("### 🔍 Search Results")
        for idx, doc in enumerate(st.session_state.related_docs):
            row = st.columns([1, 10, 1])
            with row[0]:
                if doc not in st.session_state.reference_docs:
                    if st.button("➕", key=f"add_ref_{idx}"):
                        st.session_state.reference_docs.append(doc)
                        st.experimental_rerun()
            with row[1]:
                with st.expander(
                    f"{idx+1}. {doc.get('title', 'No Title')}", expanded=False
                ):
                    st.write("**Summary:**")
                    st.write(doc.get("summary", "No summary"))
                    if st.button("🔍 View Full", key=f"view_full_{idx}"):
                        st.session_state.selected_doc_idx = idx
                        st.experimental_rerun()

with preview_col:
    st.markdown("### 📖 Document Preview")
    idx = st.session_state.get("selected_doc_idx")
    doc_list = st.session_state.reference_docs + st.session_state.related_docs
    if idx is not None and 0 <= idx < len(doc_list):
        doc = doc_list[idx]
        st.markdown(f"**{doc.get('title', 'No Title')}**")
        st.markdown("---")
        content = doc.get("content", "No content.")
        html_content = content.replace("\n", "<br>")
        st.markdown(
            f'<div class="scroll-box">{html_content}</div>', unsafe_allow_html=True
        )
        if st.button("🔙 Back"):
            st.session_state.selected_doc_idx = None
            st.experimental_rerun()
    else:
        st.info("Click a document to preview full content here.")
