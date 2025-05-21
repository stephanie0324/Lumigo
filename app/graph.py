from typing import TypedDict, List
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import BaseMessage


# 定義 state 結構
class GraphState(TypedDict):
    messages: List[BaseMessage]


def create_graph():
    model = ChatOpenAI(model="gpt-4o-mini", streaming=True)

    def call_model(state: GraphState) -> GraphState:
        response = model.invoke(state["messages"])
        return {"messages": state["messages"] + [response]}

    # 定義 workflow
    workflow = StateGraph(GraphState)  # 👈 這裡加入 state_schema
    workflow.add_node("llm", RunnableLambda(call_model))
    workflow.set_entry_point("llm")
    workflow.set_finish_point("llm")

    return workflow.compile()
