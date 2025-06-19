import os
import json
import aiofiles
import fitz
import asyncio

from utils.embedding_utils import get_text_embedding
from core.llm_chain import get_summary_async, get_tags_async
from schema.doc_schema import DocumentModel


def chunk_pdf_text(file_path: str) -> list[str]:
    doc = fitz.open(file_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    chunks = [full_text[i:i+1000] for i in range(0, len(full_text), 1000)]
    return chunks


async def load_and_process_pdf_async(file_path: str) -> list[dict]:
    chunks = chunk_pdf_text(file_path)
    summary = await get_summary_async(" ".join(chunks))

    async def process_chunk(chunk: str) -> DocumentModel:
        tags = await get_tags_async(chunk)
        return DocumentModel(
            title=os.path.basename(file_path),
            content=chunk,
            summary=summary,
            embedding=get_text_embedding(summary),
            tags=tags
        )

    docs = await asyncio.gather(*(process_chunk(chunk) for chunk in chunks))
    return [doc.dict() for doc in docs]  # dict 化供 DB insert


async def load_and_process_json_async(file_path: str) -> list[dict]:
    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
        raw = await f.read()
        publications = json.loads(raw)

    async def process_pub(pub: dict) -> DocumentModel:
        content = pub.get("publication_description", "")
        summary = await get_summary_async(content)
        tags = await get_tags_async(content)
        return DocumentModel(
            title=pub.get("title", ""),
            content=content,
            summary=summary,
            embedding=get_text_embedding(summary),
            tags=tags
        )

    docs = await asyncio.gather(*(process_pub(pub) for pub in publications))
    return [doc.dict() for doc in docs]  # dict 化供 DB insert
