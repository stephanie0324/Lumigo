"""
This module provides utility functions to update a MongoDB vector store
with preprocessed document embeddings asynchronously, and to perform
synchronous vector similarity search using MongoDB's $vectorSearch operator.

It uses two separate MongoDB clients:
- AsyncIOMotorClient for async operations (e.g., bulk insert)
- MongoClient for sync operations (e.g., vector search)
"""

import os
import uuid
import asyncio
import aiofiles
import requests
import shutil
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from datetime import datetime
from typing import List, Optional

from core.config import settings
from logger import logger
from .embedding_utils import get_text_embedding
from .data_utils import load_and_process_pdf_async, load_and_process_json_async


sync_collection = MongoClient(settings.MONGODB_URI)[settings.MONGODB_NAME][settings.COLLECTION]
async_collection = AsyncIOMotorClient(settings.MONGODB_URI)[settings.MONGODB_NAME][settings.COLLECTION]
query_history_collection = MongoClient(settings.MONGODB_URI)[settings.MONGODB_NAME]["query_history"]


async def process_file(file_path: str):
            if file_path.endswith(".pdf"):
                return await load_and_process_pdf_async(file_path)
            elif file_path.endswith(".json"):
                return await load_and_process_json_async(file_path)
            else:
                logger.warning(f"Unsupported file format: {file_path}")
                return []

async def update_db_async():
    """
    清除現有向量資料，重新從資料夾中的 PDF / JSON 載入並寫入 MongoDB。
    """
    folder = settings.RAG_FILES_FILEPATH

    try:
        await async_collection.delete_many({})
        logger.info("Cleared existing collection.")
    except Exception as e:
        logger.error(f"Failed to clear collection: {e}")
        return

    logger.info(f"Loading files from folder: {folder}")

    try:
        files = os.listdir(folder)
    except Exception as e:
        logger.error(f"Failed to list directory {folder}: {e}")
        return

    tasks = [process_file(os.path.join(folder, f)) for f in files]
    all_docs = await asyncio.gather(*tasks)

    for docs, fname in zip(all_docs, files):
        if docs:
            try:
                await async_collection.insert_many(docs)
                logger.info(f"Inserted {len(docs)} documents from {fname}")
            except Exception as e:
                logger.error(f"Failed to insert documents from {fname}: {e}")
        else:
            logger.warning(f"No documents extracted from {fname}")

    logger.info("Vector DB update completed.")


async def append_new_thesis(keyword: str, max_results: int = 5):
    """
    Search papers by keyword, fetch DOI and metadata from CrossRef,
    check open-access availability, download PDFs (named by title), and store in vector DB.
    """
    base_folder = "papers"
    unique_id = uuid.uuid4().hex
    folder = os.path.join(base_folder, unique_id)
    os.makedirs(folder, exist_ok=True)

    async def fetch_metadata_from_crossref(query: str, rows: int = 20) -> List[dict]:
        url = f"https://api.crossref.org/works?query={query}&rows={rows}"
        try:
            resp = await asyncio.to_thread(requests.get, url, timeout=30)
            resp.raise_for_status()
            items = resp.json().get("message", {}).get("items", [])
            results = []
            for item in items:
                doi = item.get("DOI")
                title = item.get("title", [""])[0].strip()
                if doi and title:
                    results.append({
                        "doi": doi,
                        "title": title
                    })
            return results
        except Exception as e:
            logger.error(f"[CrossRef] Metadata fetch error: {e}")
            return []

    async def fetch_open_access_url(doi: str) -> Optional[str]:
        url = f"https://api.openaccessbutton.org/find?doi={doi}"
        try:
            resp = await asyncio.to_thread(requests.get, url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("url_for_pdf") or data.get("url")
        except Exception as e:
            logger.warning(f"[OpenAccess] Failed for {doi}: {e}")
        return None

    async def download_pdf(paper: dict) -> Optional[str]:
        title = paper["title"]
        pdf_url = paper["pdf_url"]
        safe_name = "".join(c for c in title if c.isalnum() or c in (" ", "_")).replace(" ", "_")[:60]
        output_path = os.path.join(folder, f"{safe_name}.pdf")

        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = await asyncio.to_thread(requests.get, pdf_url, headers=headers, timeout=20)
            if resp.status_code == 200 and b"%PDF" in resp.content[:1024]:
                async with aiofiles.open(output_path, "wb") as f:
                    await f.write(resp.content)
                logger.info(f"[PDF] Downloaded: {output_path}")
                return output_path
            else:
                logger.warning(f"[PDF] Invalid or failed to download: {pdf_url}")
        except Exception as e:
            logger.error(f"[PDF] Exception for {pdf_url}: {e}")
        return None

    # === Pipeline ===
    logger.info(f"[Search] Starting metadata fetch for: {keyword}")
    papers = await fetch_metadata_from_crossref(keyword)
    if not papers:
        logger.warning("[Pipeline] No metadata found.")
        return

    logger.info(f"[CrossRef] Retrieved {len(papers)} items. Checking open access...")

    urls = await asyncio.gather(
        *(fetch_open_access_url(p["doi"]) for p in papers),
        return_exceptions=False
    )

    valid_papers = [
        {**paper, "pdf_url": url}
        for paper, url in zip(papers, urls)
        if url is not None
    ][:max_results]

    logger.info(f"[OpenAccess] {len(valid_papers)} papers with accessible PDFs.")

    pdf_paths = await asyncio.gather(
        *(download_pdf(p) for p in valid_papers)
    )
    pdf_paths = [p for p in pdf_paths if p]
    if not pdf_paths:
        logger.warning("[Pipeline] No PDFs downloaded.")
        return

    logger.info("[Parse] Processing downloaded PDFs...")
    parsed_docs = await asyncio.gather(*(process_file(path) for path in pdf_paths))

    for docs, path in zip(parsed_docs, pdf_paths):
        if docs:
            try:
                await async_collection.insert_many(docs)
                logger.info(f"[MongoDB] Inserted {len(docs)} documents from {os.path.basename(path)}")
            except Exception as e:
                logger.error(f"[MongoDB] Insertion failed for {path}: {e}")
        else:
            logger.warning(f"[Parse] No content extracted from {os.path.basename(path)}")

    if os.path.exists(folder):
        shutil.rmtree(folder)
        logger.info(f"[CleanUp] Removed temporary folder: {folder}")


def vector_search(query: str, top_k: int = 3):
    """Perform a synchronous vector similarity search using MongoDB $vectorSearch."""
    
    def deduplicate_by_title(docs, top_k: int):
        """Deduplicate documents by title, keeping the highest-score document per title."""
        seen = {}
        for doc in sorted(docs, key=lambda x: x.get("score", 0), reverse=True):
            title = doc.get("title")
            if title and title not in seen:
                seen[title] = doc
        return list(seen.values())[:top_k]
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
                "_id": 1,
                "doc_id": 1,
                "title": 1,
                "content": 1,
                "summary": 1,
                "tags": 1,
                "score": { "$meta": "vectorSearchScore" }
            }
        },
        {
            "$match": {
                "score": { "$gte": 0.8 }  # <-- Adjust threshold as needed (range is typically 0.0 to 1.0)
            }
        }
    ]


    try:
        results = list(sync_collection.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Vector search aggregation failed: {e}")
        return []

    top_results = deduplicate_by_title(results, top_k)
    logger.debug(f"Vector search results: {top_results}")
    return top_results

# ==========================================================
# Query History Functions
# ==========================================================

def save_query_history(query, titles=None, tags=None):
    doc = {
        "query": query,
        "titles": titles or [],
        "tags": tags or [],
        "timestamp": datetime.utcnow(),
    }
    try:
        query_history_collection.insert_one(doc)
    except Exception as e:
        logger.error(f"Save failed: {e}")
        

def get_query_analytics(top_k=10, start_date=None, end_date=None):
    """Fetch top query topics (tags) and top searched documents (titles) within a date range."""
    try:
        match_stage = {}
        if start_date:
            match_stage["$gte"] = datetime.combine(start_date, datetime.min.time())
        if end_date:
            match_stage["$lte"] = datetime.combine(end_date, datetime.max.time())

        base_pipeline = []
        if match_stage:
            base_pipeline.append({"$match": {"timestamp": match_stage}})

        # Top searched topics (tags)
        tags_pipeline = base_pipeline + [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": top_k},
            {"$project": {"topic": "$_id", "count": 1, "_id": 0}}
        ]
        top_tags = list(query_history_collection.aggregate(tags_pipeline))

        # Top searched documents (titles)
        titles_pipeline = base_pipeline + [
            {"$unwind": "$titles"},
            {"$group": {"_id": "$titles", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": top_k},
            {"$project": {"title": "$_id", "count": 1, "_id": 0}}
        ]
        top_titles = list(query_history_collection.aggregate(titles_pipeline))

        return top_tags, top_titles
    except Exception as e:
        logger.error(f"Failed to get query analytics: {e}")
        return [], []


def get_total_query_count(start_date=None, end_date=None):
    """Fetch the total number of queries within a date range."""
    try:
        match_query = {}
        if start_date:
            match_query["timestamp"] = {"$gte": datetime.combine(start_date, datetime.min.time())}
        if end_date:
            if "timestamp" in match_query:
                match_query["timestamp"]["$lte"] = datetime.combine(end_date, datetime.max.time())
            else:
                match_query["timestamp"] = {"$lte": datetime.combine(end_date, datetime.max.time())}

        return query_history_collection.count_documents(match_query)
    except Exception as e:
        logger.error(f"Failed to get total query count: {e}")
        return 0
    
def get_tag_trend_data(top_k=10, start_date=None, end_date=None) -> list[dict]:
    """Return daily usage counts of top_k tags (for line chart visualization)."""
    try:
        match_stage = {}
        if start_date:
            match_stage["$gte"] = datetime.combine(start_date, datetime.min.time())
        if end_date:
            match_stage["$lte"] = datetime.combine(end_date, datetime.max.time())

        match_query = {"timestamp": match_stage} if match_stage else {}

        # First get top_k tags by total counts within date range
        top_tags_pipeline = [
            {"$match": match_query},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": top_k},
            {"$project": {"tag": "$_id", "_id": 0}}
        ]
        top_tags_docs = list(query_history_collection.aggregate(top_tags_pipeline))
        top_tags = [doc["tag"] for doc in top_tags_docs]

        # Then aggregate daily counts only for those top tags
        pipeline = [
            {"$match": match_query},
            {"$unwind": "$tags"},
            {"$match": {"tags": {"$in": top_tags}}},
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                        "tag": "$tags"
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id.date": 1}},
            {
                "$project": {
                    "_id": 0,
                    "date": "$_id.date",
                    "tag": "$_id.tag",
                    "count": 1
                }
            }
        ]

        return list(query_history_collection.aggregate(pipeline))

    except Exception as e:
        logger.error(f"Failed to get tag trend data: {e}")
        return []


if __name__ == "__main__":
    asyncio.run(append_new_thesis("reinforcement learning"))