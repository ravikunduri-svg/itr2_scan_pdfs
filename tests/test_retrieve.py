import pytest
from core.retrieve import retrieve

CHUNKS = [
    {"id": 1, "doc_id": 1, "page_num": 1, "text": "gross salary total amount rupees", "filename": "form16.pdf"},
    {"id": 2, "doc_id": 1, "page_num": 2, "text": "TDS tax deducted source income", "filename": "form16.pdf"},
    {"id": 3, "doc_id": 1, "page_num": 3, "text": "perquisite value RSU stock options", "filename": "form16.pdf"},
    {"id": 4, "doc_id": 2, "page_num": 1, "text": "dividend income foreign account Fidelity", "filename": "schwab.pdf"},
    {"id": 5, "doc_id": 2, "page_num": 2, "text": "capital gains short term long term", "filename": "schwab.pdf"},
]

def test_retrieve_returns_top_k():
    result = retrieve("gross salary", CHUNKS, top_k=2)
    assert len(result) == 2

def test_retrieve_most_relevant_first():
    result = retrieve("TDS tax deducted", CHUNKS, top_k=3)
    # The TDS chunk should be ranked highest
    assert result[0]["id"] == 2

def test_retrieve_score_field_present():
    result = retrieve("salary", CHUNKS, top_k=1)
    assert "score" in result[0]
    assert isinstance(result[0]["score"], float)

def test_retrieve_empty_chunks_returns_empty():
    result = retrieve("salary", [], top_k=5)
    assert result == []

def test_retrieve_top_k_larger_than_corpus():
    result = retrieve("salary", CHUNKS, top_k=100)
    assert len(result) == len(CHUNKS)

def test_retrieve_preserves_original_fields():
    result = retrieve("dividend Fidelity", CHUNKS, top_k=1)
    assert result[0]["filename"] == "schwab.pdf"
    assert "page_num" in result[0]
    assert "doc_id" in result[0]
