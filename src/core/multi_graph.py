import re
import asyncio
from typing import Literal, TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# Assuming these prompts are defined correctly for the new agent roles
from .prompt import MODE_DECIDE_PROMPT, EXPAND_PROMPT, REFERENCE_PROMPT, RERANK_PROMPT
from .model import llm
from .agent_tools import AgentToolRegistry

MAX_ITERATIONS = 3

class GraphState(TypedDict):
    logs: dict[str, list[str]]
    iteration: int
    trace: List[str]
    reference_docs: List[dict]
    queries: List[str]
    similarities: List[float]
    mode: Literal["explore", "direct"]
    retrieved_docs: List[dict]
    final_answer: str
    original_question: str

def decide_mode(state: GraphState) -> dict:
    """
    Agent: Decides whether to go into "explore" mode for query expansion or "direct" mode for retrieval.
    """
    state["trace"].append("decide_mode")
    logs = state.setdefault("logs", {})
    logs.setdefault("decide_mode", [])

    prompt = MODE_DECIDE_PROMPT.format(question=state["original_question"])
    decision = llm.invoke([HumanMessage(content=prompt)]).content.strip().lower()
    logs["decide_mode"].append(f"LLM decision: {decision}")

    return {"mode": decision}

def route_after_decision(state: GraphState) -> Literal["expand_query", "retrieve_documents"]:
    """Router function to direct flow after mode decision."""
    if state["mode"] == "explore":
        return "expand_query"
    return "retrieve_documents"

def expand_query(state: GraphState) -> dict:
    """
    Agent: Expands the original query into multiple related queries for broader search.
    """
    state["trace"].append("expand_query")
    logs = state.setdefault("logs", {})
    logs["expand_query"] = []

    prompt = EXPAND_PROMPT.format(original_question=state["original_question"])
    expanded_content = llm.invoke([HumanMessage(content=prompt)]).content.strip()

    expanded_queries = [line.strip() for line in expanded_content.split("\n") if line.strip()]
    logs["expand_query"].extend(expanded_queries)

    return {"queries": expanded_queries}

def retrieve_documents(state: GraphState) -> dict:
    """
    Agent: Retrieves and reranks documents based on the queries.
    """
    state["trace"].append("retrieve_documents")
    logs = state.setdefault("logs", {})
    logs["retrieve_documents"] = []

    tool_registry = AgentToolRegistry()

    if state.get("reference_docs"):
        logs["retrieve_documents"].append("Using provided reference documents.")
        return {"retrieved_docs": state["reference_docs"]}

    # If queries aren't expanded, use the original question.
    queries_to_search = state.get("queries") or [state["original_question"]]

    faiss_search_tool = tool_registry.get_tool("faiss_search")
    internal_docs = faiss_search_tool.run({
        "queries": queries_to_search,
        "max_results_per_query": 10,
    })

    if not internal_docs:
        logs["retrieve_documents"].append("No documents found after all searches.")
        return {"retrieved_docs": []}

    rerank_tool = tool_registry.get_tool("document_rerank")
    top_docs = rerank_tool.run({
        "query": state["original_question"],
        "documents": internal_docs,
        "top_k": 5
    })

    logs["retrieve_documents"].append(f"Reranking selected {len(top_docs)} documents.")
    return {"retrieved_docs": top_docs}

def generate_answer(state: GraphState) -> dict:
    """
    Agent: Generates a final answer based on the retrieved documents and the original question.
    """
    state["trace"].append("generate_answer")
    logs = state.setdefault("logs", {})
    logs.setdefault("generate_answer", [])

    tool_registry = AgentToolRegistry()
    answer_tool = tool_registry.get_tool("answer_generation")
    cited_answer = answer_tool.run({
        "query": state["original_question"],
        "reference_docs": state["retrieved_docs"]
    })

    logs["generate_answer"].append(f"Generated cited answer with {len(state['retrieved_docs'])} references.")

    return {"final_answer": cited_answer}

def decide_next_step(state: GraphState) -> Literal["expand_query", "END"]:
    """
    Agent: Decides whether to continue iterating for a better answer or to finish.
    """
    state["trace"].append("decide_next_step")
    logs = state.setdefault("logs", {})
    logs.setdefault("decide_next_step", [])

    tool_registry = AgentToolRegistry()
    decision_tool = tool_registry.get_tool("decision_maker")
    decision_result = decision_tool.run({
        "answer": state["final_answer"],
        "iteration": state["iteration"],
        "max_iterations": MAX_ITERATIONS
    })

    logs["decide_next_step"].append(f"Decision: {decision_result}")

    if decision_result["continue"]:
        print(f"--- Iteration {state['iteration'] + 1}: Refining answer ---")
        return "expand_query"
    
    return END


def create_graph() -> StateGraph:
    graph = StateGraph(GraphState)
    
    graph.add_node("decide_mode", decide_mode)
    graph.add_node("expand_query", expand_query)
    graph.add_node("retrieve_documents", retrieve_documents)
    graph.add_node("generate_answer", generate_answer)

    graph.add_edge("expand_query", "retrieve_documents")
    graph.add_edge("retrieve_documents", "generate_answer")
    
    graph.add_conditional_edges(
        "decide_mode",
        route_after_decision,
        {"expand_query": "expand_query", "retrieve_documents": "retrieve_documents"}
    )
    graph.add_conditional_edges("generate_answer", decide_next_step, {"expand_query": "expand_query", END: END})
    
    graph.add_edge(START, "decide_mode")
    return graph.compile()

def build_initial_graph_state(query: str) -> GraphState:
    return {
        "original_question": query,
        "iteration": 0,
        "trace": [],
        "reference_docs": [],
        "queries": [],
        "final_answer": "",
        "similarities": [],
        "retrieved_docs": [],
        "logs": {},
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
    print("Retrieved Docs Count:", len(final_state.get("retrieved_docs", [])))
