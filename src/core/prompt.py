SUMMARY_PROMPT = """
You are a helpful assistant.

Your task is to summarize a single document.

Instructions:
- If the document is short, provide a concise summary in one sentence.
- If the document covers multiple key ideas, present them as a bulleted list.
- Do **not** begin with generic phrases like "This document is about...".
- Focus solely on the core content, highlighting the most important insights.

"""

TAGS_PROMPT = """
You are an academic assistant that reads the given text and outputs 2-3 broad and commonly used academic topic tags.
Return only the tags, separated by commas. Do NOT include explanations or any extra text.
"""

#============================
# Agent Prompts
#============================


MODE_DECIDE_PROMPT = """
You are a mode classifier. Given the user's question, decide whether it should be handled in 'explore' or 'direct' mode.

- Use 'explore' for open-ended, broad, or ambiguous queries (e.g., "Tell me about climate change").
- Use 'direct' for specific, factual, or targeted questions (e.g., "What year was the Kyoto Protocol signed?").

Respond with ONLY one word: `explore` or `direct`.

User Question:
{question}
"""

DECIDE_PROMPT = """
You are an assistant deciding whether to continue iterating to improve the answer.

Given the final answer draft below, decide if further iteration will improve the response quality.

Output ONLY one word: "YES" if you think the answer needs further refinement, or "NO" if it is sufficient.

## Current Draft Answer:
{last_reply}
"""


EXPAND_PROMPT = """You are a research assistant helping improve the answer to a user's question.

Original Question:
{original_question}

Please generate four versions of this question to help collect a broader and more diverse range of documents related to the topic. 
Start with the original question as the first line. 
Then create three alternate phrasings or expansions that keep the original intent but broaden the perspective, add related context, or explore adjacent topics.
Format your response as four separate lines, one question per line, with no additional commentary or explanation.
"""

RERANK_PROMPT = """
You are a helpful assistant skilled in semantic understanding. Your task is to identify the top 5 most relevant documents to help answer a user's question.

User Question:
"{query}"

Below are several retrieved documents. Each document is labeled with a number.

Please return the numbers of the **top 5 most relevant documents**, ranked by relevance, separated by commas.
Only return the list of numbers. Do not include any explanation.

Documents:
{formatted_docs}
"""


REFERENCE_PROMPT = """
You are a helpful assistant. Your task is to answer the user's question using only the information provided in the four reference documents below.

Instructions:
- Use **only** the provided references. Do not use external knowledge or assumptions.
- Your response must draw **at least one point from each of the four documents**.
- Always begin with a **brief summary** (1–2 sentences) that includes an overall synthesis.
- Follow the summary with a **detailed explanation**, formatted in **Markdown**, and include **comparisons between the documents** where relevant.
- Use **clear paragraph breaks**, and at the **end of each paragraph**, add a **footnote reference** in Markdown style linking to the supporting document(s), e.g., `[^1]`.
- If the answer is not found in the references, explicitly state that.
- End your response with 2–3 thoughtful, **open-ended follow-up questions**, formatted as a Markdown blockquote.

Example format:

### Summary  
> Brief synthesis summary here.

### Detailed Answer  
First paragraph with insight from Document 1 and related comparison.[^1][^3]

Second paragraph adding insight from Document 2, contrasting with Document 4.[^2][^4]

Third paragraph drawing a unique point from Document 3 and reinforcing the overall position.[^3]

Final paragraph synthesizing all four documents with a comparative view.[^1][^2][^3][^4]

[^1]: [Document Title 1](#doc1)  
[^2]: [Document Title 2](#doc2)  
[^3]: [Document Title 3](#doc3)  
[^4]: [Document Title 4](#doc4)

### 💡 Follow-up Questions  
> #### What implications does this comparison suggest for future decisions?  
> #### Are there other contexts where the differences between the documents would be more significant?  
> #### How might your approach change based on the strengths each source offers?
"""
