import os, tempfile, pytest
from db.access import (
    init_db, add_document, add_chunk, get_all_documents,
    get_chunks_for_doc, get_all_chunks, delete_document,
    add_conversation, add_message, get_messages
)

@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path

def test_init_db_creates_tables(db_path):
    import sqlite3
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"documents", "chunks", "conversations", "messages"}.issubset(tables)

def test_add_and_get_document(db_path):
    doc_id = add_document(db_path, "form16.pdf", 9)
    docs = get_all_documents(db_path)
    assert len(docs) == 1
    assert docs[0]["filename"] == "form16.pdf"
    assert docs[0]["page_count"] == 9
    assert docs[0]["id"] == doc_id

def test_add_and_get_chunks(db_path):
    doc_id = add_document(db_path, "form16.pdf", 2)
    add_chunk(db_path, doc_id, 1, "This is page one text.")
    add_chunk(db_path, doc_id, 2, "This is page two text.")
    chunks = get_chunks_for_doc(db_path, doc_id)
    assert len(chunks) == 2
    assert chunks[0]["page_num"] == 1
    assert chunks[0]["text"] == "This is page one text."

def test_get_all_chunks(db_path):
    d1 = add_document(db_path, "a.pdf", 1)
    d2 = add_document(db_path, "b.pdf", 1)
    add_chunk(db_path, d1, 1, "chunk from a")
    add_chunk(db_path, d2, 1, "chunk from b")
    all_chunks = get_all_chunks(db_path)
    assert len(all_chunks) == 2

def test_delete_document_cascades(db_path):
    doc_id = add_document(db_path, "form16.pdf", 1)
    add_chunk(db_path, doc_id, 1, "some text")
    delete_document(db_path, doc_id)
    assert get_all_documents(db_path) == []
    assert get_all_chunks(db_path) == []

def test_conversation_and_messages(db_path):
    conv_id = add_conversation(db_path)
    add_message(db_path, conv_id, "user", "What is my gross salary?")
    add_message(db_path, conv_id, "assistant", "Answer: 93,20,084\nConfidence: HIGH\nSources:\n- Document: form16.pdf, Page 5: \"(d) Total 93200840.00\"")
    msgs = get_messages(db_path, conv_id)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
