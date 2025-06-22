import streamlit as st
import streamlit.components.v1 as components
import asyncio

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
            st.session_state.trigger_rerun = True


def render_input_area():
    input_col, btn_col = st.columns([10, 1])

    with input_col:
        st.text_input(
            "User Input",
            key="user_input",
            placeholder="e.g. What is LLM orchestration?",
            label_visibility="collapsed",
        )

    if btn_col.button("Send"):
        submit_query()

def render_answer_area(graph):

    with st.expander("📜 Chat History", expanded=False):
        col1, col2 = st.columns([8, 2])
        with col1:
            html_history = """
            <div style='max-height:300px; overflow-y:auto; padding-right:10px; font-family: sans-serif;'>
            """
            for i, (q, a) in enumerate(st.session_state.history[-10:]):
                html_history += f"""
                    <div style='margin-bottom: 1em; padding: 10px; border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9;'>
                        <p style='margin: 0;'><strong>🧑‍💬 Q{i+1}:</strong> {q}</p>
                        <hr style='margin: 8px 0;'/>
                        <p style='margin: 0;'><strong>🤖 A{i+1}:</strong></p>
                        <div style='white-space: pre-wrap; color: #333;'>{a}</div>
                    </div>
                """
            html_history += "</div>"

            components.html(html_history, height=320, scrolling=True)

        with col2:
            if st.button("🗑️ Clear", key="clear_history_btn"):
                st.session_state.history = []
                st.rerun()

    if st.session_state.submitted and st.session_state.query:
        query = st.session_state.query
        st.session_state.submitted = False

        initial_state = build_initial_graph_state(query)
        initial_state["reference_docs"] = st.session_state.get("reference_docs", [])

        final_answer = ""

        timeline_container = st.empty()

        for step_output in graph.stream(initial_state, config={"streaming": True}):
            for step_name, state in step_output.items():
                trace = state.get("trace", [])
                logs_dict = state.get("logs", {})

                log_lines = []
                for step in trace:
                    step_logs = logs_dict.get(step, [])
                    if step_logs:
                        log_lines.append(f"### Step: `{step}`")
                        for entry in step_logs:
                            log_lines.append(f"- {entry}")

                timeline_container.markdown("\n".join(log_lines))

                if step_name == "agent_retrieve":
                    st.session_state.related_docs = state.get("related_docs", [])

                if step_name == "agent_synthesis":
                    final_answer = state.get("final_answer", "")
        st.success("✅ Agent execution complete!")
        
        timeline_container.empty()

        if final_answer:
            trimmed, followup = split_answer_followups(final_answer)
            st.session_state.answer = trimmed
            st.session_state.used_indices = list(extract_used_doc_indices(trimmed))
            
            def clean_answer(text):
                import re
                
                text = re.sub(r"\[\^?\d+\]", "", text)
                text = re.sub(r"\[\s*source\s*\]", "", text, flags=re.I)
        
                lines = text.splitlines()
                cleaned_lines = []
                for line in lines:
                    if re.match(r"^\s*:.*", line):  
                        continue
                    if re.match(r".*:\s*$", line):  
                        continue
                    if re.match(r"^[A-Z].{0,100}$", line.strip()):  
                        continue
                    cleaned_lines.append(line)

                content_only = "\n".join(cleaned_lines)
                content_only = re.split(r"(?i)^(references|footnotes|related reading|learn more):", content_only)[0].strip()

                return content_only

            cleaned_answer = clean_answer(trimmed)
            save_query_history(
                query,
                titles=[doc.get("title", "No Title") for doc in st.session_state.related_docs],
                tags=list(set([tag for doc in st.session_state.related_docs for tag in doc.get("tags", [])]))
            )
            

            st.session_state.history.append((query, cleaned_answer))

            st.markdown("## 🤖 Final Answer")
            st.markdown(trimmed)

            followups = extract_followups(followup)
            if followups:
                st.markdown("### 💡 Follow-up Questions")
                for i, q in enumerate(followups):
                    st.button(q, key=f"followup_{i}", on_click=trigger_question, args=(q,))
        else:
            st.warning("⚠️ No meaningful output from the agent.")



def render_reference_docs():
    st.markdown("### 📄 Docs")
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
                        st.rerun()
        else:
            st.info("No reference documents selected.")


def render_related_docs():
    if st.session_state.related_docs:
        st.markdown("### 🔍 Source Documents")
        for idx in st.session_state.used_indices:
            if idx >= len(st.session_state.related_docs):
                continue
            doc = st.session_state.related_docs[idx]
            cols = st.columns([1, 1, 10])
            with cols[0]:
                if st.button("➕", key=f"add_ref_{idx}"):
                    if doc not in st.session_state.reference_docs:
                        st.session_state.reference_docs.append(doc)
                        st.rerun()
            with cols[2]:
                with st.expander(f"[{idx+1}] {doc.get('title', 'No Title')}"):
                    st.write("**Summary:**")
                    content = doc.get("content", "")
                    preview = content[:500] + "..." if len(content) > 500 else content
                    st.write(preview)


def main_content():
    init_state_with_history() 
    render_sidebar()
    main_col, preview_col = st.columns([2, 1])
    with main_col:
        render_input_area()
        graph = get_graph()
        render_answer_area(graph)
    with preview_col:
        render_reference_docs()
        render_related_docs()


if __name__ == "__main__":
    main_content()
