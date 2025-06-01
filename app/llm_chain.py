from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# 使用非同步 LLM 客戶端
llm = ChatOpenAI(model="gpt-4o-mini", streaming=False)

summary_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant that summarizes the given context. "
            "DO NOT add any explanations, extra text, or punctuation.",
        ),
        ("human", "{input_text}"),
    ]
)

tags_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an academic assistant that reads the given text and outputs 2-3 broad and commonly used academic topic tags. "
            "Return only the tags, separated by commas. Do NOT include explanations or any extra text.",
        ),
        ("human", "{input_text}"),
    ]
)

async def get_summary_async(input_text: str) -> str:
    """Asynchronously generate a summary of the input text."""
    chain = summary_prompt | llm
    response = await chain.ainvoke({"input_text": input_text})
    return response.content.strip()

async def get_tags_async(input_text: str) -> list[str]:
    """Asynchronously extract tags from the input text."""
    chain = tags_prompt | llm
    response = await chain.ainvoke({"input_text": input_text})
    tags_str = response.content.strip()
    return [tag.strip() for tag in tags_str.split(",") if tag.strip()]
