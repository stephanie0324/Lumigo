from typing import Literal, TypedDict, List
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


from utils.embedding_utils import get_text_embedding, cosine_sim, format_docs_for_prompt
from utils.db_utils import vector_search
from .prompt import DECIDE_PROMPT, EXPAND_PROMPT, REFERENCE_PROMPT
from .model import llm

MAX_ITERATIONS = 3

class GraphState(TypedDict):
    messages: List[BaseMessage]
    iteration: int
    trace: List[str]
    reference_docs: List[dict]
    answers: List[str]
    queries: List[str]
    similarities: List[float]
    mode: Literal["explore", "direct"]
    related_docs: List[dict]

# ===== Agent Nodes =====
def agent_start(state: GraphState) -> Command[Literal["agent_expand", "agent_retrieve"]]:
    state["trace"].append("agent_start")
    # trace 是修改了，但也要放到 update
    return Command(
        goto="agent_expand" if state["mode"] == "explore" else "agent_retrieve",
        update={"trace": state["trace"]}
    )


def agent_expand(state: GraphState) -> Command[Literal["agent_retrieve"]]:
    state["trace"].append("agent_expand")
    prompt = EXPAND_PROMPT.format(original_question=state["messages"][0].content)
    expanded = llm.invoke([HumanMessage(content=prompt)]).content

    return Command(
        goto="agent_retrieve",
        update={"messages": [AIMessage(content=expanded)], "trace": state["trace"]}
    )


def agent_retrieve(state: GraphState) -> Command[Literal["agent_decide"]]:
    state["trace"].append("agent_retrieve")
    query = state["messages"][-1].content
    state["queries"].append(query)

    sim = cosine_sim(get_text_embedding(query), get_text_embedding(state["messages"][0].content))
    state["similarities"].append(sim)

    docs = state["reference_docs"] or vector_search(query) or []
    state["related_docs"].extend(docs)

    formatted = format_docs_for_prompt(docs)
    messages = [
        SystemMessage(content=REFERENCE_PROMPT),
        HumanMessage(content=f"Reference:\n{formatted}\n\nQuestion: {query}"),
    ]
    answer = llm.invoke(messages).content
    state["answers"].append(answer)

    return Command(
        goto="agent_decide",
        update={
            "messages": [AIMessage(content=answer)],
            "trace": state["trace"],
            "queries": state["queries"],
            "similarities": state["similarities"],
            "related_docs": state["related_docs"],
            "answers": state["answers"],
        }
    )


def agent_decide(state: GraphState) -> Command[Literal["agent_expand", END]]:
    state["trace"].append("agent_decide")
    if state["iteration"] >= MAX_ITERATIONS:
        return Command(goto=END, update={"trace": state["trace"]})

    prompt = DECIDE_PROMPT.format(last_reply=state["messages"][-1].content)
    decision = llm.invoke([HumanMessage(content=prompt)]).content.strip().upper()
    next_iter = state["iteration"] + 1

    update_dict = {"trace": state["trace"]}
    if "YES" in decision:
        update_dict["iteration"] = next_iter

    return Command(
        goto="agent_expand" if "YES" in decision else END,
        update=update_dict
    )

# ===== Graph Construction =====

def create_graph(mode: Literal["explore", "direct"]) -> StateGraph:
    graph = StateGraph(GraphState)
    graph.add_node("agent_start", agent_start)
    graph.add_node("agent_expand", agent_expand)
    graph.add_node("agent_retrieve", agent_retrieve)
    graph.add_node("agent_decide", agent_decide)
    graph.set_entry_point("agent_start")
    graph.set_finish_point("agent_decide")
    return graph.compile()

# ===== Initial State Builder =====

def build_initial_graph_state(query: str, mode: Literal["explore", "direct"] = "explore") -> GraphState:
    return {
        "messages": [HumanMessage(content=query)],
        "iteration": 0,
        "trace": [],
        "reference_docs": [],
        "answers": [],
        "queries": [],
        "similarities": [],
        "mode": mode,
        "related_docs": [],
    }


# ===== Main Execution =====

if __name__ == "__main__":
    query = "What are the latest advancements in AI?"
    mode = "explore" 
    
    state = build_initial_graph_state(query, mode)
    graph = create_graph(mode)

    print("Initial State:", state)

    print("\n--- Final State ---")
    print("Trace:", state["trace"])
    print("Answers:", state["answers"])
    print("Iterations:", state["iteration"])
    print("Queries:", state["queries"])
    print("Related Docs:", state["related_docs"])
    print("Similarities:", state["similarities"])