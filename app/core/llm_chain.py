from langchain_core.prompts import ChatPromptTemplate

from .model import llm
from .prompt import SUMMARY_PROMPT, TAGS_PROMPT

async def get_summary_async(input_text: str) -> str:
    """Asynchronously generate a summary of the input text."""
    summary_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SUMMARY_PROMPT.strip()),
            ("human", "{input_text}"),
        ]
    )
    chain = summary_prompt | llm
    response = await chain.ainvoke({"input_text": input_text})
    return response.content.strip()

async def get_tags_async(input_text: str) -> list[str]:
    """Asynchronously extract tags from the input text."""
    tags_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", TAGS_PROMPT.strip()),
            ("human", "{input_text}"),
        ]
    )
    chain = tags_prompt | llm
    response = await chain.ainvoke({"input_text": input_text})
    tags_str = response.content.strip()
    return [tag.strip() for tag in tags_str.split(",") if tag.strip()]
