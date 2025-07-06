import re
import asyncio
from typing import Literal, TypedDict, List
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


from logger import logger
from utils.embedding_utils import format_docs_for_prompt
from utils.db_utils import vector_search, append_new_thesis
from .prompt import MODE_DECIDE_PROMPT, DECIDE_PROMPT, EXPAND_PROMPT, REFERENCE_PROMPT, RERANK_PROMPT
from .model import llm

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

# ===== Agent Nodes =====
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

    # Use reference_docs if provided
    if state.get("reference_docs"):
        state["related_docs"] = state["reference_docs"]
        logs["agent_retrieve"].append("Using provided reference documents.")
        return Command(goto="agent_cite", update=state)

    expanded_text = state["messages"][-1].content
    expanded_queries = [line.strip() for line in expanded_text.split("\n") if line.strip()]
    state["queries"].extend(expanded_queries)

    def search_and_dedup(queries: list[str]) -> list[dict]:
        logger.info("[Search] Starting vector search...")
        all_docs = []
        for q in queries:
            docs = vector_search(q) or []
            all_docs.extend(docs)
        logs["agent_retrieve"].append(f"Retrieved {len(all_docs)} documents total.")
        unique = {doc["_id"]: doc for doc in all_docs}
        logger.info(f"[Search] {len(unique)} unique documents after dedup.")
        return list(unique.values())

    # Step 1: Internal vector search
    internal_docs = search_and_dedup(expanded_queries)

    # Step 2: Fallback to Thesis search if no internal docs found
    if len(internal_docs) < 5:
        logs["agent_retrieve"].append("Too few docs found. Falling back to thesis search...")

        async def fetch_and_store_all():
            await asyncio.gather(*(append_new_thesis(k, max_results=5) for k in expanded_queries))

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In async context, spawn task
                loop.create_task(fetch_and_store_all())
            else:
                asyncio.run(fetch_and_store_all())

            logs["agent_retrieve"].append("Thesis fetch completed.")
        except Exception as e:
            logger.error(f"[Fallback] Failed to append new thesis: {e}")
            logs["agent_retrieve"].append("Thesis fetch failed.")


    if not internal_docs:
        logs["agent_retrieve"].append("Still no documents found after fallback.")
        state["related_docs"] = []
        return Command(goto="agent_cite", update=state)

    # Step 3: Rerank
    formatted = "\n\n".join(f"[{i+1}] {doc['summary']}" for i, doc in enumerate(internal_docs))
    prompt = RERANK_PROMPT.format(query=state["messages"][0].content, formatted_docs=formatted)
    response = llm.invoke([HumanMessage(content=prompt)]).content.strip()

    indices = [int(i) for i in re.findall(r"\d+", response) if 1 <= int(i) <= len(internal_docs)]
    top_docs = [internal_docs[i - 1] for i in indices[:5]] if indices else [internal_docs[0]]

    logs["agent_retrieve"].append(
        f"Selected {len(top_docs)} documents based on rerank." if indices else "Fallback to first document."
    )

    state["related_docs"] = top_docs
    return Command(goto="agent_cite", update=state)


def agent_cite(state: GraphState) -> Command:
    state["trace"].append("agent_cite")
    logs = state.setdefault("logs", {})
    logs.setdefault("agent_cite", [])

    formatted = format_docs_for_prompt(state["related_docs"])
    messages = [SystemMessage(content=REFERENCE_PROMPT),
                HumanMessage(content=f"Reference:\n{formatted}\n\nQuestion: {state['queries'][-1]}")]

    cited_answer = llm.invoke(messages).content

    state["answers"].append(cited_answer)

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

    if state["iteration"] >= MAX_ITERATIONS:
        logs["agent_decide"].append("Max iterations reached, ending.")
        return Command(goto=END, update={"trace": state["trace"], "logs": logs})

    prompt = DECIDE_PROMPT.format(last_reply=state["final_answer"])
    decision = llm.invoke([HumanMessage(content=prompt)]).content.strip().upper()

    next_iter = state["iteration"] + 1

    update_dict = {"trace": state["trace"], "logs": logs}
    if "YES" in decision:
        update_dict["iteration"] = next_iter
    logs["agent_decide"].append(f"Need expand for better reasoning: {decision}")
    return Command(
        goto="agent_expand" if "YES" in decision else END,
        update=update_dict
    )

# ===== Graph Construction =====
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

# ===== Initial State Builder =====
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



# ===== Main Execution =====
if __name__ == "__main__":
    query = "What are the latest advancements in AI?"
    state = build_initial_graph_state(query)
    graph = create_graph()

    final_state = graph.invoke(state)

    print("--- Final State ---")
    print("Trace:", final_state["trace"])
    print("Answers:", final_state["answers"])
    print("Iterations:", final_state["iteration"])
    print("Queries:", final_state["queries"])
    print("Related Docs:", final_state["related_docs"])
    print("Similarities:", final_state["similarities"])
