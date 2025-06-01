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
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings
from logger import logger
from data_preporocess import load_and_process_pdf_async, load_and_process_json_async
from utils import get_text_embedding


# 同步 client，用於 vector_search 這類同步查詢
sync_client = MongoClient(settings.MONGODB_URI)
sync_db = sync_client[settings.MONGODB_NAME]
sync_collection = sync_db[settings.COLLECTION]

# 非同步 client，用於資料匯入、清除等非同步操作
async_client = AsyncIOMotorClient(settings.MONGODB_URI)
async_db = async_client[settings.MONGODB_NAME]
async_collection = async_db[settings.COLLECTION]


async def process_file(file_path):
    if file_path.endswith(".pdf"):
        return await load_and_process_pdf_async(file_path)
    elif file_path.endswith(".json"):
        return await load_and_process_json_async(file_path)
    else:
        logger.warning(f"❗ Unsupported file format: {file_path}")
        return []


async def update_db_async():
    logger.info("🧹 Clearing existing collection asynchronously...")
    await async_collection.delete_many({})

    logger.info("📂 Reading source documents asynchronously...")
    data_folder = settings.RAG_FILES_FILEPATH

    tasks = []
    for file in os.listdir(data_folder):
        file_path = os.path.join(data_folder, file)
        tasks.append(process_file(file_path))

    all_docs = await asyncio.gather(*tasks)

    for docs, file in zip(all_docs, os.listdir(data_folder)):
        if docs:
            await async_collection.insert_many(docs)
            logger.info(f"✅ Inserted {len(docs)} documents from {file}")

    logger.info("🎉 Vector DB async update completed.")


def vector_search(query: str, top_k: int = 5):
    """
    Perform a vector similarity search in MongoDB synchronously using $vectorSearch.

    Args:
        query (str): The input query text.
        top_k (int): Number of top similar documents to return.

    Returns:
        List[Dict]: Top matching documents with similarity score.
    """
    query_vector = get_text_embedding(query)

    pipeline = [
        {
            "$vectorSearch": {
                "queryVector": query_vector,
                "path": "embedding",
                "numCandidates": 500,
                "limit":500,
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

    raw_results = list(sync_collection.aggregate(pipeline))
    
    def deduplicate_by_title(raw_results, top_k=20):
        """
        Deduplicate vector search results by title, keeping the highest-score document per title.
        """
        title_to_doc = {}

        for doc in raw_results:
            title = doc["title"]
            score = doc.get("score", 0)

            if title not in title_to_doc or score > title_to_doc[title].get("score", 0):
                title_to_doc[title] = doc

        # Sort by score descending and limit to top_k
        deduped_sorted = sorted(title_to_doc.values(), key=lambda d: d.get("score", 0), reverse=True)
        return deduped_sorted[:top_k]

    # dedulicate results by title
    final_results = deduplicate_by_title(raw_results, top_k)
    logger.debug(f"Vector Searched Docs: {final_results}'")
    return final_results
