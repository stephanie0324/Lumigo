import streamlit as st
from graph import create_graph

# 建立圖形
graph = create_graph()

st.title("LangGraph + Streamlit RAG 助手")

# 使用 session_state 儲存對話歷史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 顯示對話歷史
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 使用者輸入
if prompt := st.chat_input("請輸入您的問題："):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 執行圖形
    state = {"user_input": prompt}
    result = graph.invoke(state)
    response = result.get("response", "")

    st.chat_message("assistant").write(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
