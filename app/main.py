import streamlit as st
from langchain_core.messages import HumanMessage
from graph import create_graph  # Your custom LangGraph pipeline

# Page settings
st.set_page_config(page_title="KnowBot", page_icon="🤖", layout="centered")
st.title("KnowBot")

# Create LangGraph instance
graph = create_graph()

# Initialize session state
if "input_key" not in st.session_state:
    st.session_state.input_key = "input_0"
if "submitted" not in st.session_state:
    st.session_state.submitted = False


# Simple generator to stream only the LLM output tokens
def stream_response(prompt):
    messages = [HumanMessage(content=prompt)]
    for output in graph.stream(
        {"messages": messages},
        config={
            "streaming": True,
        },
    ):
        # Assume output has structure like {'messages': [...]} and last message is LLM
        final_message = output.get("messages")[-1]
        yield final_message.content


# Handle input submission
def submit_input():
    st.session_state.submitted = True


# Input field
user_input = st.text_input(
    "Ask KnowBot:",
    key=st.session_state.input_key,
    placeholder="Type your question and press Enter...",
    label_visibility="collapsed",
    on_change=submit_input,
)

# On input submitted
if st.session_state.submitted:
    prompt = user_input.strip()
    if prompt:
        # Show user message
        st.chat_message("user").write(prompt)

        # Stream assistant reply
        with st.chat_message("assistant"):
            st.write_stream(stream_response(prompt))

    # Reset state
    idx = int(st.session_state.input_key.split("_")[1])
    st.session_state.input_key = f"input_{idx + 1}"
    st.session_state.submitted = False
    st.rerun()
