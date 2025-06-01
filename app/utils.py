# file: utils/embedding_helper.py

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from config import settings

# 初始化 embedding model（只要初始化一次）
_embedding_model = HuggingFaceBgeEmbeddings(
    **settings.RAG_INDEX_HF_EMBEDDING_MODEL_CONFIG
)


def get_text_embedding(text: str) -> list[float]:
    """
    Generate an embedding vector for the given text.

    Args:
        text (str): Input text to embed.

    Returns:
        list[float]: Embedding vector.
    """
    return _embedding_model.embed_query(text)


def format_docs_for_prompt(docs):
    formatted = []
    for i, doc in enumerate(docs):
        title = doc.get("title", "No Title")
        content = doc.get("content", "No content.")
        doc_text = f"[Doc: {i+1}] Title: {title}\nContent:\n{content}\n\n---"
        formatted.append(doc_text)
    return "\n".join(formatted)
