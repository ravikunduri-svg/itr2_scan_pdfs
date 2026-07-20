import os, tempfile, pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.ingest import extract_pages, ingest_pdf
from db.access import init_db, get_all_documents, get_all_chunks

# --- extract_pages ---

def test_extract_pages_returns_list_of_dicts():
    """extract_pages returns [{page_num, text}] for non-blank pages."""
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page one content"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "   "  # blank — should be skipped
    mock_page3 = MagicMock()
    mock_page3.extract_text.return_value = "Page three content"

    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page1, mock_page2, mock_page3]

    with patch("pdfplumber.open", return_value=mock_pdf):
        result = extract_pages("dummy.pdf")

    assert len(result) == 2
    assert result[0] == {"page_num": 1, "text": "Page one content"}
    assert result[1] == {"page_num": 3, "text": "Page three content"}

def test_extract_pages_passes_password():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "text"
    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open", return_value=mock_pdf) as mock_open:
        extract_pages("doc.pdf", password="secret")
        mock_open.assert_called_once_with("doc.pdf", password="secret")

def test_extract_pages_no_password_passes_none():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "text"
    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open", return_value=mock_pdf) as mock_open:
        extract_pages("doc.pdf", password="")
        mock_open.assert_called_once_with("doc.pdf", password=None)

# --- ingest_pdf ---

def test_ingest_pdf_stores_document_and_chunks(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)

    pages = [
        {"page_num": 1, "text": "Salary details here"},
        {"page_num": 2, "text": "TDS deducted amount"},
    ]
    with patch("core.ingest.extract_pages", return_value=pages):
        doc_id = ingest_pdf("dummy.pdf", "form16.pdf", db_path)

    docs = get_all_documents(db_path)
    assert len(docs) == 1
    assert docs[0]["filename"] == "form16.pdf"
    assert docs[0]["page_count"] == 2

    chunks = get_all_chunks(db_path)
    assert len(chunks) == 2
    assert chunks[0]["text"] == "Salary details here"
    assert chunks[1]["page_num"] == 2

def test_ingest_pdf_returns_doc_id(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)

    with patch("core.ingest.extract_pages", return_value=[{"page_num": 1, "text": "hello"}]):
        doc_id = ingest_pdf("dummy.pdf", "ais.pdf", db_path)

    assert isinstance(doc_id, int)
    assert doc_id > 0
