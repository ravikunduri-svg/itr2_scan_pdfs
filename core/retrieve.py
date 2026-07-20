import re
from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> list:
    return re.findall(r"\b\w+\b", text.lower())


def retrieve(query: str, chunks: list, top_k: int = 5) -> list:
    """Return top_k chunks most relevant to query, sorted by BM25 score descending."""
    if not chunks:
        return []

    corpus = [_tokenize(c["text"]) for c in chunks]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(_tokenize(query))

    k = min(top_k, len(chunks))
    ranked = sorted(
        [{"score": float(scores[i]), **chunks[i]} for i in range(len(chunks))],
        key=lambda x: x["score"],
        reverse=True,
    )
    return ranked[:k]
