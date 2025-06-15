
import re
import asyncio
import streamlit as st
from multi_graph import create_graph, build_initial_graph_state, MAX_ITERATIONS
from vectorDB import update_db_async
from prompt import SUMMARY_PROMPT, REFERENCE_PROMPT


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
                asyncio.run(update_db_async())
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
        st.checkbox("🔎 Explore mode (expand your queries at least once)", key="explore_mode")

    if btn_col.button("Send"):
        submit_query()

def render_answer_area(graph):
    if st.session_state.submitted and st.session_state.query:
        query = st.session_state.query
        st.session_state.submitted = False

        mode = "explore" if st.session_state.explore_mode else "direct"
        initial_state = build_initial_graph_state(query, mode)
        initial_state["reference_docs"] = st.session_state.reference_docs
        
        final_answer = ""

        with st.expander("🧩 Agent Execution Steps", expanded=False):
            for step_output in graph.stream(initial_state, config={"streaming": True}):
                for step_name, state in step_output.items():
                    st.write(f"Step: `{step_name}`")

                    if step_name == "agent_retrieve":
                        messages = state.get("messages", [])
                        if messages:
                            final_answer = messages[-1].content

                        st.session_state.related_docs = state.get("related_docs", [])

        st.success("✅ Agent execution complete!")

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
                        init_state.reference_docs.pop(idx)
                        st.session_state.trigger_rerun = True
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
    render_sidebar()
    main_col, preview_col = st.columns([2, 1])
    with main_col:
        render_input_area()
        graph = create_graph(st.session_state.explore_mode)
        render_answer_area(graph)
    with preview_col:
        render_reference_docs()
        render_related_docs()
