import re
import asyncio
from typing import Literal, TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from logger import logger
from utils.embedding_utils import format_docs_for_prompt
from utils.db_utils import vector_search, append_new_thesis
from .prompt import MODE_DECIDE_PROMPT, DECIDE_PROMPT, EXPAND_PROMPT, REFERENCE_PROMPT, RERANK_PROMPT
from .model import llm

MAX_ITERATIONS = 3

# =========================
# Tool Input Schemas
# =========================

class VectorSearchInput(BaseModel):
    queries: List[str] = Field(description="List of search queries")
    max_results_per_query: int = Field(default=10, description="Maximum results per query")
    deduplicate: bool = Field(default=True, description="Whether to deduplicate results")

class ThesisSearchInput(BaseModel):
    queries: List[str] = Field(description="List of search queries")
    max_results: int = Field(default=5, description="Maximum results per query")

class DocumentRerankInput(BaseModel):
    query: str = Field(description="Original query for relevance scoring")
    documents: List[Dict[str, Any]] = Field(description="Documents to rerank")
    top_k: int = Field(default=5, description="Number of top documents to return")

class AnswerGenerationInput(BaseModel):
    query: str = Field(description="Query to answer")
    reference_docs: List[Dict[str, Any]] = Field(description="Reference documents for citation")
    prompt_template: str = Field(default=REFERENCE_PROMPT, description="Prompt template to use")

class DecisionInput(BaseModel):
    answer: str = Field(description="Current answer to evaluate")
    iteration: int = Field(description="Current iteration count")
    max_iterations: int = Field(default=MAX_ITERATIONS, description="Maximum allowed iterations")
    decision_prompt: str = Field(default=DECIDE_PROMPT, description="Prompt for decision making")

# =========================
# Tools
# =========================

class VectorSearchTool(BaseTool):
    name: str = Field(default="vector_search")
    description: str = Field(default="Search for relevant documents using vector similarity")
    args_schema: type[BaseModel] = VectorSearchInput

    def _run(self, queries: List[str], max_results_per_query: int = 10, deduplicate: bool = True) -> List[Dict[str, Any]]:
        logger.info(f"[VectorSearchTool] Searching for {len(queries)} queries")

        all_docs = []
        for query in queries:
            docs = vector_search(query) or []
            all_docs.extend(docs[:max_results_per_query])

        if deduplicate:
            unique_docs = {doc["_id"]: doc for doc in all_docs}
            result = list(unique_docs.values())
            logger.info(f"[VectorSearchTool] Found {len(result)} unique documents after dedup")
        else:
            result = all_docs

        return result

    async def _arun(self, queries: List[str], max_results_per_query: int = 10, deduplicate: bool = True) -> List[Dict[str, Any]]:
        return self._run(queries, max_results_per_query, deduplicate)


class ThesisSearchTool(BaseTool):
    name: str = Field(default="thesis_search")
    description: str = Field(default="Fetch and store thesis documents as fallback search")
    args_schema: type[BaseModel] = ThesisSearchInput

    def _run(self, queries: List[str], max_results: int = 5) -> Dict[str, Any]:
        logger.info(f"[ThesisSearchTool] Fetching thesis documents for {len(queries)} queries")

        async def fetch_all():
            await asyncio.gather(*(append_new_thesis(q, max_results=max_results) for q in queries))
            return {"status": "completed", "queries_processed": len(queries)}

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = loop.create_task(fetch_all())
                return {"status": "task_created", "queries_processed": len(queries)}
            else:
                result = asyncio.run(fetch_all())
                return result
        except Exception as e:
            logger.error(f"[ThesisSearchTool] Failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _arun(self, queries: List[str], max_results: int = 5) -> Dict[str, Any]:
        logger.info(f"[ThesisSearchTool] Async fetching thesis documents for {len(queries)} queries")
        try:
            await asyncio.gather(*(append_new_thesis(q, max_results=max_results) for q in queries))
            return {"status": "completed", "queries_processed": len(queries)}
        except Exception as e:
            logger.error(f"[ThesisSearchTool] Async failed: {e}")
            return {"status": "failed", "error": str(e)}


class DocumentRerankTool(BaseTool):
    name: str = Field(default="document_rerank")
    description: str = Field(default="Rerank documents based on query relevance using LLM")
    args_schema: type[BaseModel] = DocumentRerankInput

    def _run(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"[DocumentRerankTool] Reranking {len(documents)} documents for query: {query[:50]}...")
        if not documents:
            return []

        formatted = "\n\n".join(f"[{i+1}] {doc.get('summary', doc.get('content', '')[:200])}" for i, doc in enumerate(documents))
        prompt = RERANK_PROMPT.format(query=query, formatted_docs=formatted)
        response = llm.invoke([HumanMessage(content=prompt)]).content.strip()

        indices = [int(i) for i in re.findall(r"\d+", response) if 1 <= int(i) <= len(documents)]

        if indices:
            top_docs = [documents[i - 1] for i in indices[:top_k]]
            logger.info(f"[DocumentRerankTool] Selected {len(top_docs)} documents based on rerank")
        else:
            top_docs = [documents[0]]
            logger.info(f"[DocumentRerankTool] Fallback to first document")

        return top_docs

    async def _arun(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        return self._run(query, documents, top_k)


class AnswerGenerationTool(BaseTool):
    name: str = Field(default="answer_generation")
    description: str = Field(default="Generate answers with proper citations from reference documents")
    args_schema: type[BaseModel] = AnswerGenerationInput

    def _run(self, query: str, reference_docs: List[Dict[str, Any]], prompt_template: str = REFERENCE_PROMPT) -> str:
        logger.info(f"[AnswerGenerationTool] Generating answer for query: {query[:50]}...")

        formatted_docs = format_docs_for_prompt(reference_docs)
        messages = [
            SystemMessage(content=prompt_template),
            HumanMessage(content=f"Reference:\n{formatted_docs}\n\nQuestion: {query}")
        ]
        cited_answer = llm.invoke(messages).content
        logger.info(f"[AnswerGenerationTool] Generated answer with {len(reference_docs)} references")
        return cited_answer

    async def _arun(self, query: str, reference_docs: List[Dict[str, Any]], prompt_template: str = REFERENCE_PROMPT) -> str:
        return self._run(query, reference_docs, prompt_template)


class DecisionTool(BaseTool):
    name: str = Field(default="decision_maker")
    description: str = Field(default="Make decisions about whether to continue or end the workflow")
    args_schema: type[BaseModel] = DecisionInput

    def _run(self, answer: str, iteration: int, max_iterations: int = MAX_ITERATIONS, decision_prompt: str = DECIDE_PROMPT) -> Dict[str, Any]:
        logger.info(f"[DecisionTool] Making decision at iteration {iteration}/{max_iterations}")

        if iteration >= max_iterations:
            return {
                "continue": False,
                "reason": "max_iterations_reached",
                "next_action": "end"
            }

        prompt = decision_prompt.format(last_reply=answer)
        decision = llm.invoke([HumanMessage(content=prompt)]).content.strip().upper()
        continue_workflow = "YES" in decision

        return {
            "continue": continue_workflow,
            "reason": "llm_decision",
            "decision_text": decision,
            "next_action": "expand" if continue_workflow else "end"
        }

    async def _arun(self, answer: str, iteration: int, max_iterations: int = MAX_ITERATIONS, decision_prompt: str = DECIDE_PROMPT) -> Dict[str, Any]:
        return self._run(answer, iteration, max_iterations, decision_prompt)


# =========================
# Tool Registry
# =========================

class AgentToolRegistry:
    """Registry for managing agent tools"""

    def __init__(self):
        self.tools = {}
        self._initialize_tools()

    def _initialize_tools(self):
        tools = [
            VectorSearchTool(),
            ThesisSearchTool(),
            DocumentRerankTool(),
            AnswerGenerationTool(),
            DecisionTool()
        ]
        for tool in tools:
            self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())
