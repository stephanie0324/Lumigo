
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI
from typing import List
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

from google.cloud import aiplatform
from vertexai.preview.language_models import TextEmbeddingModel


from .config import settings

aiplatform.init(project=settings.PROJECT_ID, location=settings.LOCATION)

# chatgpt or vertexai
if len(settings.PROJECT_ID) and len(settings.LOCATION):
    llm = ChatVertexAI(
        model_name="gemini-2.0-flash-001",
        temperature=0.7,
        streaming=False
    )
else:
    llm = ChatOpenAI(model="gpt-4o-mini", streaming=False)
    
class EmbeddingModelWrapper:
    def __init__(self):
        if len(settings.PROJECT_ID) and len(settings.LOCATION):
            self.use_vertexai = True
            self.model = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")
        else:
            self.use_vertexai = False
            self.model = HuggingFaceBgeEmbeddings(**settings.RAG_INDEX_HF_EMBEDDING_MODEL_CONFIG)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if self.use_vertexai:
            # The Vertex AI model expects a list of strings.
            response = self.model.get_embeddings(texts)
            # The response is a list of TextEmbedding objects, so we extract the 'values' from each.
            return [embedding.values for embedding in response]
        else:
            # The HuggingFace model also expects a list of strings.
            return self.model.embed_documents(texts)

embedding_model = EmbeddingModelWrapper()
