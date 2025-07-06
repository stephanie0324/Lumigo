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


EXPAND_PROMPT = """You are a research assistant improving the answer to a user’s question.

Original Question:
{original_question}

Write four versions of this question:
- First, the original question as is.
- Then, three rephrased or expanded versions that keep the intent but broaden or explore related topics.
Format as four lines, one question per line, no extra comments.
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
You are a helpful assistant in an academic exploration platform. Your task is to answer the user's question using **only** the information provided in the four reference documents below.

---

### 📘 Instructions

- Use **only** the four provided reference documents. Do **not** use any external knowledge or assumptions.
- Your answer must reference **at least one point from each document**, with comparisons and synthesis when relevant.
- Begin with a **short, direct summary** (1–2 sentences) that **answers the user’s question**, not a summary of the documents.
- Follow with a **detailed explanation** using Markdown:
  - Use **bold** for key concepts or claims  
  - Use `<span style="background-color:#fef08a">` to highlight key sentences  
  - Use `<span style="color:#1d4ed8">` or `<span style="color:#059669">` for emphasis  
  - Break into clear, readable paragraphs
- At the **end of each paragraph**, include source references as footnotes like `[^1]`.
- Conclude with 2–3 **open-ended follow-up questions** to encourage deeper exploration.
- Format is designed for **Streamlit** using `unsafe_allow_html=True`.

---
Format Example:

### 📌 TL;DR
> <span style="background-color:#e0f7fa; padding:10px 14px; border-radius:6px; display:block;">
> Multi-agent systems improve recommendation systems by enabling specialized collaboration, dynamic adaptation, and explainable results.
> </span>


#### Detailed Answer  
First paragraph with insight from Document 1 and related comparison.[^1][^3]

Second paragraph adding insight from Document 2, contrasting with Document 4.[^2][^4]

Third paragraph drawing a unique point from Document 3 and reinforcing the overall position.[^3]

Final paragraph synthesizing all four documents with a comparative view.[^1][^2][^3][^4]

[^1]: [Document Title 1](#doc1)  
[^2]: [Document Title 2](#doc2)  
[^3]: [Document Title 3](#doc3)  
[^4]: [Document Title 4](#doc4)

#### 💡 Follow-up Questions  
> #### What implications does this comparison suggest for future decisions?  
> #### Are there other contexts where the differences between the documents would be more significant?  
> #### How might your approach change based on the strengths each source offers?
"""
