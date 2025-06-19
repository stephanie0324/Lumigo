import streamlit as st
import asyncio

from core.backend import (
    init_state, submit_query, trigger_question,
    extract_used_doc_indices, split_answer_followups,
    extract_followups, get_graph, async_update_db
)
from core.multi_graph import build_initial_graph_state  # 這裡單獨引入



    
def render_sidebar():
    st.sidebar.header("📘 How to use KnowBot")
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
    st.markdown("### 💬 Ask KnowBot")
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
    if st.session_state.submitted and st.session_state.query:
        query = st.session_state.query
        st.session_state.submitted = False

        initial_state = build_initial_graph_state(query)
        initial_state["reference_docs"] = st.session_state.get("reference_docs", [])

        final_answer = ""

        # Reserve a placeholder for streaming logs
        timeline_container = st.empty()

        for step_output in graph.stream(initial_state, config={"streaming": True}):
            for step_name, state in step_output.items():
                # Extract trace and logs dict
                trace = state.get("trace", [])
                logs_dict = state.get("logs", {})

                # Build incremental log text from trace and logs_dict
                log_lines = []
                for step in trace:
                    step_logs = logs_dict.get(step, [])
                    if step_logs:
                        log_lines.append(f"### Step: `{step}`")
                        for entry in step_logs:
                            log_lines.append(f"- {entry}")

                # Update the timeline_container with current logs as markdown
                timeline_container.markdown("\n".join(log_lines))

                # Save final answer when synthesis step is reached
                if step_name == "agent_synthesis":
                    final_answer = state.get("final_answer", "")
                    st.session_state.related_docs = state.get("related_docs", [])
        st.success("✅ Agent execution complete!")
        
        timeline_container.empty()  # Clear the placeholder after execution

        # Optionally render the full timeline widget once at the end:
        if final_answer:
            trimmed, followup = split_answer_followups(final_answer)
            st.session_state.answer = trimmed
            st.session_state.used_indices = list(extract_used_doc_indices(trimmed))

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
    init_state()
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
