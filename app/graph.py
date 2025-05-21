import os
from langgraph.graph import StateGraph, END
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()


# 定義狀態
class State(dict):
    pass


# 定義節點函數
def generate_response(state: State) -> State:
    user_input = state.get("user_input", "")
    llm = ChatOpenAI(model_name="gpt-4", temperature=0.7)
    messages = [
        SystemMessage(content="你是一個有幫助的助理。"),
        HumanMessage(content=user_input),
    ]
    response = llm(messages)
    state["response"] = response.content
    return state


# 建立圖形
def create_graph():
    workflow = StateGraph(State)
    workflow.add_node("generate_response", generate_response)
    workflow.set_entry_point("generate_response")
    workflow.set_finish_point("generate_response")
    return workflow.compile()
