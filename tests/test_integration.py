# tests/test_integration.py
"""
Integration tests — real BM25, mocked Grok API.
No real PDFs required; text is injected directly via db.access.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from db.access import init_db, add_document, add_chunk, get_all_documents


@pytest.fixture
def app_with_data(tmp_path):
    db_path = str(tmp_path / "test.db")
    upload_dir = str(tmp_path / "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    init_db(db_path)

    # Seed two documents with known text
    doc1 = add_document(db_path, "form16.pdf", 3)
    add_chunk(db_path, doc1, 5, "(d) Total 93200840.00 gross salary")
    add_chunk(db_path, doc1, 6, "Value of perquisites under section 17(2)")
    add_chunk(db_path, doc1, 8, "Tax Deducted from Salary of Employee u/s 192(1) 3,57,73,078.00")

    doc2 = add_document(db_path, "ais.pdf", 1)
    add_chunk(db_path, doc2, 1, "Annual Information Statement dividend interest")

    app = create_app(db_path)
    app.config["UPLOAD_FOLDER"] = upload_dir
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c, db_path


def _mock_grok(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_bm25_retrieves_relevant_chunk_for_salary(app_with_data):
    """BM25 should rank the salary chunk first for 'gross salary' query."""
    from core.retrieve import retrieve
    from db.access import get_all_chunks
    _, db_path = app_with_data
    chunks = get_all_chunks(db_path)
    results = retrieve("gross salary", chunks, top_k=3)
    assert results[0]["page_num"] == 5
    assert "93200840" in results[0]["text"]


def test_ask_endpoint_returns_answer(app_with_data):
    client, _ = app_with_data
    grok_answer = (
        "Answer: Your gross salary is Rs 93,20,084.\n"
        "Confidence: HIGH\n"
        "Sources:\n- Document: form16.pdf, Page 5: \"(d) Total 93200840.00\""
    )
    with patch.dict(os.environ, {"GROK_API_KEY": "test-key"}):
        with patch("core.answer.OpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create.return_value = _mock_grok(grok_answer)
            resp = client.post("/ask", json={"question": "What is my gross salary?"})

    assert resp.status_code == 200
    data = resp.get_json()
    assert "Answer:" in data["answer"]
    assert "HIGH" in data["answer"]


def test_ask_stores_messages_in_history(app_with_data):
    client, _ = app_with_data
    grok_answer = "Answer: Rs 93,20,084.\nConfidence: HIGH\nSources:\n- Document: form16.pdf, Page 5: \"...\""
    with patch.dict(os.environ, {"GROK_API_KEY": "test-key"}):
        with patch("core.answer.OpenAI") as mock_cls:
            mock_cls.return_value.chat.completions.create.return_value = _mock_grok(grok_answer)
            client.post("/ask", json={"question": "salary?"})

    hist_resp = client.get("/history")
    history = hist_resp.get_json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "salary?"
    assert history[1]["role"] == "assistant"


def test_delete_removes_document(app_with_data):
    client, db_path = app_with_data
    docs = get_all_documents(db_path)
    doc_id = docs[0]["id"]
    resp = client.post(f"/delete/{doc_id}")
    assert resp.status_code == 302
    remaining = get_all_documents(db_path)
    assert all(d["id"] != doc_id for d in remaining)


def test_ask_no_docs_returns_no_docs_message(tmp_path):
    """When no documents are uploaded, answer returns the NO_DOCS_RESPONSE."""
    db_path = str(tmp_path / "empty.db")
    upload_dir = str(tmp_path / "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    init_db(db_path)
    app = create_app(db_path)
    app.config["UPLOAD_FOLDER"] = upload_dir
    app.config["TESTING"] = True
    with app.test_client() as c:
        with patch.dict(os.environ, {"GROK_API_KEY": "test-key"}):
            resp = c.post("/ask", json={"question": "What is my salary?"})
    data = resp.get_json()
    assert "No documents" in data["answer"]
