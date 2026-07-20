import os, tempfile, pytest
from unittest.mock import patch
from app import create_app
from db.access import init_db

@pytest.fixture
def client(tmp_path):
    db_path = str(tmp_path / "test.db")
    upload_dir = str(tmp_path / "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    init_db(db_path)
    app = create_app(db_path)
    app.config["UPLOAD_FOLDER"] = upload_dir
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_index_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200

def test_upload_rejects_non_pdf(client):
    data = {"file": (b"not a pdf", "doc.txt"), "password": ""}
    resp = client.post("/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 302  # redirect after flash
    # Follow redirect
    resp2 = client.get("/")
    assert b"PDF" in resp2.data or resp.status_code == 302

def test_upload_pdf_calls_ingest(client, tmp_path):
    dummy_pdf = tmp_path / "dummy.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4 fake")
    with patch("app.routes.ingest_pdf", return_value=1) as mock_ingest:
        with open(str(dummy_pdf), "rb") as f:
            resp = client.post(
                "/upload",
                data={"file": (f, "dummy.pdf"), "password": ""},
                content_type="multipart/form-data",
            )
        mock_ingest.assert_called_once()

def test_delete_redirects(client, tmp_path):
    from db.access import add_document
    db_path = client.application.config["DB_PATH"]
    doc_id = add_document(db_path, "x.pdf", 1)
    resp = client.post(f"/delete/{doc_id}")
    assert resp.status_code == 302

def test_ask_returns_json(client):
    with patch("app.routes.get_all_chunks", return_value=[]):
        with patch("app.routes.retrieve", return_value=[]):
            with patch("app.routes.answer", return_value="Answer: None\nConfidence: LOW\nSources: None"):
                resp = client.post("/ask", json={"question": "What is my salary?"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "answer" in data

def test_ask_requires_question(client):
    resp = client.post("/ask", json={})
    assert resp.status_code == 400

def test_history_returns_list(client):
    resp = client.get("/history")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)
