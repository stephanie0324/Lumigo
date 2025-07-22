import re
import json
import faiss
import numpy as np
from typing import Literal, TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_openai import OpenAIEmbeddings
from logger import logger
from utils.embedding_utils import format_docs_for_prompt # Assuming this utility exists and is correct
from .prompt import DECIDE_PROMPT, REFERENCE_PROMPT, RERANK_PROMPT
from .model import llm, embedding_model

MAX_ITERATIONS = 3

# =========================
# Tool Input Schemas
# =========================

class FaissSearchInput(BaseModel):
    queries: List[str] = Field(description="List of search queries")
    max_results_per_query: int = Field(default=10, description="Maximum results per query")

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

class FaissSearchTool(BaseTool):
    name: str = Field(default="faiss_search")
    description: str = Field(default="Search for relevant documents using a local FAISS index.")
    args_schema: type[BaseModel] = FaissSearchInput

    index: Any = Field(default=None, exclude=True)
    metadata: List[dict] = Field(default_factory=list, exclude=True)
    embeddings: Any = Field(default=None, exclude=True)

    def __init__(self, index_path="storage/vector_index.faiss", metadata_path="storage/metadata.json", **kwargs):
        super().__init__(**kwargs)
        try:
            self.index = faiss.read_index(index_path)
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            self.embeddings = embedding_model
            logger.info(f"FAISS index and metadata loaded successfully from {index_path}")
        except Exception as e:
            logger.error(f"Failed to load FAISS index or metadata: {e}")
            # Handle initialization failure, maybe raise an error or set a flag
            self.index = None

    def _run(self, queries: List[str], max_results_per_query: int = 10) -> List[dict]:
        if self.index is None:
            logger.error("FAISS index is not available.")
            return []

        all_retrieved_docs = []
        all_retrieved_indices = set()

        for query in queries:
            query_embedding = self.embeddings.get_embeddings([query])[0]
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            _distances, indices = self.index.search(query_vector, max_results_per_query)
            
            for doc_index in indices[0]:
                if doc_index != -1 and doc_index not in all_retrieved_indices:
                    all_retrieved_indices.add(doc_index)
                    retrieved_doc = self.metadata[doc_index]
                    # Ensure the entire document object is returned, not just content
                    # The metadata already contains page_content and metadata keys.
                    all_retrieved_docs.append(retrieved_doc) 
        
        logger.info(f"FAISS search found {len(all_retrieved_docs)} unique documents.")
        return all_retrieved_docs


class DocumentRerankTool(BaseTool):
    name: str = Field(default="document_rerank")
    description: str = Field(default="Rerank documents based on query relevance using LLM")
    args_schema: type[BaseModel] = DocumentRerankInput

    def _run(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"[DocumentRerankTool] Reranking {len(documents)} documents for query: {query[:50]}...")
        if not documents:
            return []

        formatted = "\n\n".join(f"[{i+1}] {doc.get('summary', doc.get('page_content', '')[:200])}" for i, doc in enumerate(documents))
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
            FaissSearchTool(),
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
