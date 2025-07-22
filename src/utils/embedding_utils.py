# file: utils/embedding_helper.py

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from typing import List
import numpy as np

from core.config import settings
from core.model import embedding_model


def get_text_embedding(text: str) -> list[float]:
    """
    Generate an embedding vector for the given text.

    Args:
        text (str): Input text to embed.

    Returns:
        list[float]: Embedding vector.
    """
    # The embedding model expects a list of texts.
    embeddings = embedding_model.get_embeddings([text])
    return embeddings[0] if embeddings else []

def cosine_sim(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def format_docs_for_prompt(docs):
    return "\n".join(
    f"[Doc: {i+1}] Title: {doc.get('metadata', {}).get('source', 'No Title')}\nContent:\n{doc.get('page_content', 'No content.')}\n\n---"
    for i, doc in enumerate(docs)
)
