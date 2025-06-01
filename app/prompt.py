SUMMARY_PROMPT = """
You are a helpful assistant.

Your task is to summarize a single document.

Instructions:
- If the document is short, provide a concise summary in one sentence.
- If the document covers multiple key ideas, present them as a bulleted list.
- Do **not** begin with generic phrases like "This document is about...".
- Focus solely on the core content, highlighting the most important insights.

"""

REFERENCE_PROMPT = """
You are a helpful assistant. Your task is to answer the user's question using **only** the information provided in the reference documents below.

Each reference is formatted as:
[Doc {i+1}] Title: {title}
Content:
{content}
---
  
Guidelines:
- Use only the information from the reference documents. Do **not** use any external knowledge or assumptions.
- When citing specific information, use the document number in square brackets, e.g., [1], [2], etc.
- If the answer is not present in the references, respond clearly with:  
  "The answer is not available in the provided reference documents."
- Make your answer detailed, structured, and focused on the question.
- When appropriate, end with a thoughtful follow-up question to encourage further exploration.

References:
{references}

Question:
{question}

"""
