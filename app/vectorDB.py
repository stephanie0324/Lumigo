"""
This module provides a utility function to update a MongoDB vector store
with preprocessed document embeddings. If the collection already contains data,
it will skip re-importing.

It also includes a vector_search function to perform similarity search
using MongoDB's $vectorSearch operator, intended for RAG workflows.
"""

import json
from pymongo import MongoClient
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from config import settings
from logger import logger
from utils import get_text_embedding

client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_NAME]
collection = db[settings.COLLECTION]


def update_db():
    """
    Update MongoDB vector store with embedded documents.

    This function checks if the specified MongoDB collection is empty.
    If it is, it reads a local JSON file (configured via settings), processes
    each document to generate embeddings using HuggingFaceBgeEmbeddings, and
    inserts the resulting documents into the MongoDB collection.

    If the collection already contains documents, it logs a message and skips update.

    Expected document format in JSON:
    [
        {
            "id": "unique_id",
            "title": "Title of document",
            "publication_description": "Main content of document"
        },
        ...
    ]
    """

    if collection.count_documents({}) > 0:
        logger.info("MongoDB already contains vector documents. Skipping update.")
        return

    logger.info("No vectors found. Updating and generating embeddings...")

    with open(settings.RAG_FILES_FILEPATH, "r", encoding="utf-8") as f:
        articles = json.load(f)

    for article in articles:
        doc_id = article["id"]
        title = article.get("title", "")
        content = article.get("publication_description", "")
        full_text = f"{title}\n\n{content}"

        embedding = get_text_embedding(full_text)

        document = {
            "doc_id": doc_id,
            "title": title,
            "content": full_text,
            "embedding": embedding,
        }

        collection.insert_one(document)

    logger.info("Vector update completed.")


def vector_search(query: str, top_k: int = 5):
    """
    Perform a vector similarity search in MongoDB using $vectorSearch.

    Args:
        query (str): The input query text.
        top_k (int): Number of top similar documents to return.

    Returns:
        List[Dict]: Top matching documents with similarity.
    """
    query_vector = get_text_embedding(query)

    pipeline = [
        {
            "$vectorSearch": {
                "queryVector": query_vector,
                "path": "embedding",
                "numCandidates": 100,
                "limit": top_k,
                "index": settings.INDEX_NAME,
            }
        },
        {
            "$project": {
                "_id": 0,
                "doc_id": 1,
                "title": 1,
                "content": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    results = list(collection.aggregate(pipeline))
    logger.info(f"Vector search returned {len(results)} results.")
    return results
