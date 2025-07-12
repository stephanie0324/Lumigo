import re
import asyncio
from typing import Literal, TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from .prompt import MODE_DECIDE_PROMPT, DECIDE_PROMPT, EXPAND_PROMPT, REFERENCE_PROMPT, RERANK_PROMPT
from .model import llm
from .agent_tools import AgentToolRegistry

MAX_ITERATIONS = 3

class GraphState(TypedDict):
    logs: dict[str, list[str]]
    messages: List[BaseMessage]
    iteration: int
    trace: List[str]
    reference_docs: List[dict]
    answers: List[str]
    queries: List[str]
    similarities: List[float]
    mode: Literal["explore", "direct"]
    related_docs: List[dict]
    draft: str
    final_answer: str

def agent_start(state: GraphState) -> Command[Literal["agent_expand", "agent_retrieve"]]:
    state["trace"].append("agent_start")
    logs = state.setdefault("logs", {})
    logs.setdefault("agent_start", [])

    prompt = MODE_DECIDE_PROMPT.format(question=state["messages"][0].content)
    decision = llm.invoke([HumanMessage(content=prompt)]).content.strip().lower()
    logs["agent_start"].append(f"LLM decision: {decision}")

    next_node = "agent_expand" if decision == "explore" else "agent_retrieve"

    return Command(
        goto=next_node,
        update={
            "trace": state["trace"],
            "mode": decision,
            "logs": logs
        }
    )

def agent_expand(state: GraphState) -> Command:
    state["trace"].append("agent_expand")
    logs = state.setdefault("logs", {})
    logs["agent_expand"] = []

    prompt = EXPAND_PROMPT.format(original_question=state["messages"][0].content)
    expanded = llm.invoke([HumanMessage(content=prompt)]).content.strip()

    lines = [line.strip() for line in expanded.split("\n") if line.strip()]
    logs["agent_expand"].extend(lines)

    return Command(
        goto="agent_retrieve",
        update={
            "messages": [AIMessage(content=expanded)],
            "trace": state["trace"],
            "logs": logs
        }
    )

def agent_retrieve(state: GraphState) -> Command:
    state["trace"].append("agent_retrieve")
    logs = state.setdefault("logs", {})
    logs["agent_retrieve"] = []
    state.setdefault("queries", [])

    tool_registry = AgentToolRegistry()

    if state.get("reference_docs"):
        state["related_docs"] = state["reference_docs"]
        logs["agent_retrieve"].append("Using provided reference documents.")
        return Command(goto="agent_cite", update=state)

    expanded_text = state["messages"][-1].content
    expanded_queries = [line.strip() for line in expanded_text.split("\n") if line.strip()]
    state["queries"].extend(expanded_queries)

    vector_search_tool = tool_registry.get_tool("vector_search")
    internal_docs = vector_search_tool.run({
        "queries": expanded_queries,
        "max_results_per_query": 10,
        "deduplicate": True
    })

    logs["agent_retrieve"].append(f"Vector search returned {len(internal_docs)} documents.")

    if len(internal_docs) < 5:
        logs["agent_retrieve"].append("Too few docs found. Using thesis search fallback...")
        thesis_search_tool = tool_registry.get_tool("thesis_search")
        thesis_result = thesis_search_tool.run({
            "queries": expanded_queries,
            "max_results": 5
        })
        logs["agent_retrieve"].append(f"Thesis search status: {thesis_result.get('status', 'unknown')}")
        internal_docs = vector_search_tool.run({
            "queries": expanded_queries,
            "max_results_per_query": 10,
            "deduplicate": True
        })

    if not internal_docs:
        logs["agent_retrieve"].append("No documents found after all searches.")
        state["related_docs"] = []
        return Command(goto="agent_cite", update=state)

    rerank_tool = tool_registry.get_tool("document_rerank")
    top_docs = rerank_tool.run({
        "query": state["messages"][0].content,
        "documents": internal_docs,
        "top_k": 5
    })

    logs["agent_retrieve"].append(f"Reranking selected {len(top_docs)} documents.")
    state["related_docs"] = top_docs
    return Command(goto="agent_cite", update=state)

def agent_cite(state: GraphState) -> Command:
    state["trace"].append("agent_cite")
    logs = state.setdefault("logs", {})
    logs.setdefault("agent_cite", [])

    tool_registry = AgentToolRegistry()
    answer_tool = tool_registry.get_tool("answer_generation")
    cited_answer = answer_tool.run({
        "query": state["queries"][-1] if state["queries"] else state["messages"][0].content,
        "reference_docs": state["related_docs"]
    })

    state["answers"].append(cited_answer)
    logs["agent_cite"].append(f"Generated cited answer with {len(state['related_docs'])} references.")

    return Command(goto="agent_synthesis", update={
        "answers": state["answers"],
        "trace": state["trace"],
        "logs": logs
    })

def agent_synthesis(state: GraphState) -> Command:
    state["trace"].append("agent_synthesis")
    logs = state.setdefault("logs", {})
    logs.setdefault("agent_synthesis", [])

    final_answer = state["answers"][-1]

    return Command(goto="agent_decide", update={
        "final_answer": final_answer,
        "trace": state["trace"],
        "logs": logs
    })

def agent_decide(state: GraphState) -> Command:
    state["trace"].append("agent_decide")
    logs = state.setdefault("logs", {})
    logs.setdefault("agent_decide", [])

    tool_registry = AgentToolRegistry()
    decision_tool = tool_registry.get_tool("decision_maker")
    decision_result = decision_tool.run({
        "answer": state["final_answer"],
        "iteration": state["iteration"],
        "max_iterations": MAX_ITERATIONS
    })

    logs["agent_decide"].append(f"Decision: {decision_result}")
    update_dict = {"trace": state["trace"], "logs": logs}

    if decision_result["continue"]:
        update_dict["iteration"] = state["iteration"] + 1
        next_node = "agent_expand"
    else:
        next_node = END

    return Command(goto=next_node, update=update_dict)

def create_graph() -> StateGraph:
    graph = StateGraph(GraphState)
    graph.add_node("agent_start", agent_start)
    graph.add_node("agent_expand", agent_expand)
    graph.add_node("agent_retrieve", agent_retrieve)
    graph.add_node("agent_cite", agent_cite)
    graph.add_node("agent_synthesis", agent_synthesis)
    graph.add_node("agent_decide", agent_decide)
    graph.set_entry_point("agent_start")
    graph.set_finish_point("agent_decide")
    return graph.compile()

def build_initial_graph_state(query: str) -> GraphState:
    return {
        "messages": [HumanMessage(content=query)],
        "iteration": 0,
        "trace": [],
        "reference_docs": [],
        "answers": [],
        "queries": [],
        "similarities": [],
        "related_docs": [],
    }

if __name__ == "__main__":
    query = "What are the latest advancements in AI?"
    state = build_initial_graph_state(query)
    graph = create_graph()

    final_state = graph.invoke(state)

    print("--- Final State ---")
    print("Trace:", final_state["trace"])
    print("Final Answer:", final_state.get("final_answer", "No answer generated"))
    print("Iterations:", final_state["iteration"])
    print("Related Docs Count:", len(final_state.get("related_docs", [])))
