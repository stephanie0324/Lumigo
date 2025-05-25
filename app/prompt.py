SUMMARY_PROMPT = """
You are a helpful assistant.
If the document is short, summarize it in 1 concise sentence.
If it contains multiple key ideas, list them clearly using bullet points.
Avoid using phrases like "The document is about." Focus only on the core content.
"""

REFERENCE_PROMPT = """
You are a helpful assistant. Answer the user's question in a detailed and informative way based only on the provided reference documents.
Ensure the response is complete and well-structured, covering all relevant aspects found in the references.
If the answer cannot be found in the references, clearly say so.

When possible, end your response with a thoughtful follow-up question to encourage deeper exploration or continued conversation.
"""
