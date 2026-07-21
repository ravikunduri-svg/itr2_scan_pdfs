from openai import OpenAI

NO_DOCS_RESPONSE = (
    "Answer: No documents have been uploaded yet.\n"
    "Confidence: LOW\n"
    "Sources: None"
)

_SYSTEM_PROMPT = """\
You are a financial document assistant. Answer the user's question using ONLY the document excerpts provided.

Rules:
1. Never invent numbers or facts not present in the excerpts.
2. If the answer is not in the excerpts, say "The information is not available in the uploaded documents."
3. Always respond in EXACTLY this format (no deviation):

Answer: <your answer>
Confidence: HIGH|MEDIUM|LOW
Sources:
- Document: <filename>, Page <N>: "<exact quote from excerpt>"

Confidence guide:
- HIGH: exact figures found verbatim in the text
- MEDIUM: answer requires inference from multiple excerpts
- LOW: answer not clearly supported by the excerpts
"""


def _build_context(chunks: list) -> str:
    parts = []
    for c in chunks:
        parts.append(f"[Document: {c['filename']}, Page {c['page_num']}]\n{c['text']}")
    return "\n\n---\n\n".join(parts)


def answer(question: str, chunks: list, api_key: str) -> str:
    """Call Groq API with question + retrieved chunks. Returns structured answer string."""
    if not chunks:
        return NO_DOCS_RESPONSE

    context = _build_context(chunks)
    user_message = f"Document excerpts:\n\n{context}\n\nQuestion: {question}"

    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
        )
        return response.choices[0].message.content
    except Exception as exc:
        return f"Answer: Unable to generate answer ({type(exc).__name__}: {exc})\nConfidence: LOW\nSources: None"
