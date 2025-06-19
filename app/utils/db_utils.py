"""
This module provides utility functions to update a MongoDB vector store
with preprocessed document embeddings asynchronously, and to perform
synchronous vector similarity search using MongoDB's $vectorSearch operator.

It uses two separate MongoDB clients:
- AsyncIOMotorClient for async operations (e.g., bulk insert)
- MongoClient for sync operations (e.g., vector search)
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from core.config import settings
from logger import logger
from utils.embedding_utils import get_text_embedding
from utils.data_utils import load_and_process_pdf_async, load_and_process_json_async


sync_collection = MongoClient(settings.MONGODB_URI)[settings.MONGODB_NAME][settings.COLLECTION]
async_collection = AsyncIOMotorClient(settings.MONGODB_URI)[settings.MONGODB_NAME][settings.COLLECTION]


async def process_file(file_path: str):
    """Process a single file depending on its extension."""
    if file_path.endswith(".pdf"):
        return await load_and_process_pdf_async(file_path)
    elif file_path.endswith(".json"):
        return await load_and_process_json_async(file_path)
    else:
        logger.warning(f"Unsupported file format: {file_path}")
        return []


async def update_db_async():
    """Clear the vector DB and reload it from PDF/JSON files asynchronously."""
    try:
        await async_collection.delete_many({})
        logger.info("Cleared existing collection.")
    except Exception as e:
        logger.error(f"Failed to clear collection: {e}")
        return

    folder = settings.RAG_FILES_FILEPATH
    logger.info(f"Loading files from folder: {folder}")

    try:
        files = os.listdir(folder)
    except Exception as e:
        logger.error(f"Failed to list directory {folder}: {e}")
        return

    tasks = [process_file(os.path.join(folder, f)) for f in files]
    all_docs = await asyncio.gather(*tasks)

    for docs, f in zip(all_docs, files):
        if docs:
            try:
                await async_collection.insert_many(docs)
                logger.info(f"Inserted {len(docs)} documents from {f}")
            except Exception as e:
                logger.error(f"Failed to insert documents from {f}: {e}")
        else:
            logger.warning(f"No documents extracted from {f}")

    logger.info("Vector DB update completed.")


def deduplicate_by_title(docs, top_k: int):
    """Deduplicate documents by title, keeping the highest-score document per title."""
    seen = {}
    for doc in sorted(docs, key=lambda x: x.get("score", 0), reverse=True):
        title = doc.get("title")
        if title and title not in seen:
            seen[title] = doc
    return list(seen.values())[:top_k]


def vector_search(query: str, top_k: int = 3):
    """Perform a synchronous vector similarity search using MongoDB $vectorSearch."""
    query_vec = get_text_embedding(query)

    pipeline = [
        {
            "$vectorSearch": {
                "queryVector": query_vec,
                "path": "embedding",
                "numCandidates": 500,
                "limit": 500,
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

    try:
        results = list(sync_collection.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Vector search aggregation failed: {e}")
        return []

    top_results = deduplicate_by_title(results, top_k)
    logger.debug(f"Vector search results: {top_results}")
    return top_results
