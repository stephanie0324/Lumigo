
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI
from google.cloud import aiplatform


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