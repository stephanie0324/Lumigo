from pydantic import BaseModel, Field
from typing import List


class DocumentModel(BaseModel):
    title: str = Field(..., description="Title of the document")
    content: str = Field(..., description="Text content or chunk")
    summary: str = Field(..., description="LLM-generated summary")
    embedding: List[float] = Field(..., description="Embedding vector of the content")
    tags: List[str] = Field(default_factory=list, description="Optional tags or labels")
