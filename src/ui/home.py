import streamlit as st
import streamlit.components.v1 as components
import asyncio
from datetime import datetime

from core.backend import (
    init_state, submit_query, trigger_question,
    extract_used_doc_indices, split_answer_followups,
    extract_followups, get_graph, async_update_db
)
from core.multi_graph import build_initial_graph_state 
from utils.db_utils import save_query_history

def init_state_with_history():
    init_state()
    if "history" not in st.session_state:
        st.session_state.history = []
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "query" not in st.session_state:
        st.session_state.query = ""
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    if "reference_docs" not in st.session_state:
        st.session_state.reference_docs = []
    if "related_docs" not in st.session_state:
        st.session_state.related_docs = []
    if "used_indices" not in st.session_state:
        st.session_state.used_indices = []
    if "selected_doc_idx" not in st.session_state:
        st.session_state.selected_doc_idx = None

def render_sidebar():
    st.sidebar.header("📘 How to use Lumigo")
    st.sidebar.markdown("👉 For full instructions, go to the **Help** page.")
    st.sidebar.info(
        "**Quick Steps:**\n"
        "1. Enter a question\n"
        "2. Search & save articles\n"
        "3. Add references\n"
        "4. Ask using references"
    )

    with st.sidebar.expander("🛠️ Developer Tools (WIP)"):
        st.markdown("*The following feature is under development.*")
        if st.button("🔄 Update Vector DB"):
            with st.spinner("Updating database..."):
                asyncio.run(async_update_db())
            st.success("Database update complete ✅")
            st.experimental_rerun()

def render_title():
    st.markdown("""
        <div style='text-align:center; margin: 1rem 0 2rem 0;'>
            <div style='font-size:2.8rem; font-weight:700; text-shadow: 1px 1px 3px rgba(0,0,0,0.1); color:#222;'>
                Lumigo (.◜◡◝)
            </div>
            <p style='font-size:1.2rem; color:#666; margin-top:0.3rem;'>
                Your calm, intelligent assistant for academic reasoning
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_input_area():

    input_col, btn_col = st.columns([10, 1])
    with input_col:
        user_input = st.text_input(
            "User Input",
            value=st.session_state.query,
            key="user_input",
            placeholder="e.g. What is LLM orchestration?",
            label_visibility="collapsed",
            on_change=lambda: setattr(st.session_state, "query", st.session_state.user_input)
        )
    if btn_col.button("Send"):
        st.session_state.query = st.session_state.user_input
        st.session_state.submitted = True

    st.markdown("</div>", unsafe_allow_html=True)

def render_answer_area(graph):
    with st.expander("📜 Chat History", expanded=False):
        col1, col2 = st.columns([8, 2])
        with col1:
            html_history = """
            <div style='max-height:300px; overflow-y:auto; padding-right:10px;'>
            """
            for i, (q, a) in enumerate(st.session_state.history[-10:]):
                html_history += f"""
                    <div style='margin-bottom: 1.2em; padding: 1rem 1.2rem; background: #fffef8;
                        border-left: 4px solid #ffd84d; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.03);'>
                        <p><strong>Q{i+1}:</strong> {q}</p>
                        <p style='margin-top: 0.6em;'><strong>A{i+1}:</strong> {a}</p>
                    </div>
                """
            html_history += "</div>"
            components.html(html_history, height=320, scrolling=True)

        with col2:
            if st.button("🗑️ Clear", key="clear_history_btn"):
                st.session_state.history.clear()
                st.experimental_rerun()

    if st.session_state.submitted and st.session_state.query:
        query = st.session_state.query
        st.session_state.submitted = False

        initial_state = build_initial_graph_state(query)
        initial_state["reference_docs"] = st.session_state.reference_docs
        initial_state["queries"] = [query]

        final_answer = ""
        timeline_container = st.empty()

        with st.spinner("Running agent..."):
            for step_output in graph.stream(initial_state, config={"streaming": True}):
                for step_name, state in step_output.items():
                    if step_name == "agent_retrieve":
                        st.session_state.related_docs = state.get("related_docs", [])
                    if step_name == "agent_synthesis":
                        final_answer = state.get("final_answer", "")

        timeline_container.empty()
        st.success("✅ Agent execution complete!")

        if final_answer:
            trimmed, followup = split_answer_followups(final_answer)
            st.session_state.answer = trimmed
            st.session_state.used_indices = list(extract_used_doc_indices(trimmed))

            def clean_answer(text):
                import re
                text = re.sub(r"\[^\d+\]", "", text)
                text = re.sub(r"\[\s*source\s*\]", "", text, flags=re.I)
                lines = text.splitlines()
                return "\n".join(
                    line for line in lines
                    if not re.match(r"^\s*:.*", line) and
                       not re.match(r".*:\s*$", line) and
                       not re.match(r"^[A-Z].{0,100}$", line.strip())
                ).strip()

            cleaned_answer = clean_answer(trimmed)
            save_query_history(
                query,
                titles=[doc.get("title", "No Title") for doc in st.session_state.related_docs],
                tags=list(set([tag for doc in st.session_state.related_docs for tag in doc.get("tags", [])]))
            )
            st.session_state.history.append((query, cleaned_answer))

            st.markdown("""
                <div style='background-color:#fffef4; padding: 1.2rem 1.5rem; border-left: 5px solid #ffe066;
                            border-radius: 10px; margin-top: 1.5rem; box-shadow: 0 1px 6px rgba(0,0,0,0.03);'>
            """, unsafe_allow_html=True)
            st.markdown(cleaned_answer, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            followups = extract_followups(followup)
            if followups:
                st.markdown("#### 💡 Follow-up Questions")
                for i, q in enumerate(followups):
                    st.button(q, key=f"followup_{i}", on_click=trigger_question, args=(q,))
        else:
            st.warning("⚠️ No meaningful output from the agent.")

def render_reference_docs():
    with st.expander("📚 Reference Documents", expanded=True):
        if st.session_state.reference_docs:
            for idx, doc in enumerate(st.session_state.reference_docs):
                cols = st.columns([9, 1])
                with cols[0]:
                    if st.button(doc.get("title", f"Document {idx+1}"), key=f"ref_doc_{idx}"):
                        st.session_state.selected_doc_idx = idx
                with cols[1]:
                    if st.button("❌", key=f"remove_ref_{idx}"):
                        st.session_state.reference_docs.pop(idx)
                        st.experimental_rerun()
        else:
            st.info("No reference documents selected.")

def render_related_docs():
    if st.session_state.related_docs:
        st.markdown("#### 🔍 Source Documents")
        for idx in st.session_state.used_indices:
            if idx >= len(st.session_state.related_docs):
                continue
            doc = st.session_state.related_docs[idx]
            cols = st.columns([1, 1, 10])
            with cols[0]:
                if st.button("➕", key=f"add_ref_{idx}"):
                    if doc not in st.session_state.reference_docs:
                        st.session_state.reference_docs.append(doc)
                        st.experimental_rerun()
            with cols[2]:
                with st.expander(f"[{idx+1}] {doc.get('title', 'No Title')}"):
                    st.write("**Summary:**")
                    content = doc.get("content", "")
                    preview = content[:500] + "..." if len(content) > 500 else content
                    st.write(preview)

def render_ans_snippet():
    def generate_note_markdown(question, answer, references: list[dict]) -> str:
        note = f"# Question\n{question}\n\n"
        note += f"## Answer\n{answer}\n\n"
        note += "## References\n"
        for ref in references:
            note += f"- **Title:** \"{ref.get('title', 'No Title')}\"\n"
            note += f"  - Section: {ref.get('section', 'N/A')}\n"
            content = ref.get("content", "")
            preview = content[:200] + "..." if len(content) > 200 else content
            note += f"  - Chunk: {preview}\n\n"
        note += f"## Date\n{datetime.today().date()}\n"
        return note

    if ("answer" in st.session_state and "query" in st.session_state
        and "reference_docs" in st.session_state):
        question = st.session_state.query
        answer = st.session_state.answer
        selected_refs = st.session_state.reference_docs

        md_string = generate_note_markdown(question, answer, selected_refs)
        with st.expander("📝 View Notes Summary"):
            st.code(md_string, language='markdown')
            st.download_button("📥 Download as .md", data=md_string, file_name="note.md", mime="text/markdown")

def main_content():
    init_state_with_history()
    render_sidebar()

    render_title()

    main_col, preview_col = st.columns([2, 1])
    with main_col:
        render_input_area()
        graph = get_graph()
        render_answer_area(graph)

    with preview_col:
        render_ans_snippet()
        render_reference_docs()
        render_related_docs()

if __name__ == "__main__":
    main_content()
