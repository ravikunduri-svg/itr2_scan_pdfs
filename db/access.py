import sqlite3
from pathlib import Path


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    schema = (Path(__file__).parent / "schema.sql").read_text()
    conn = _connect(db_path)
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


def add_document(db_path: str, filename: str, page_count: int) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO documents (filename, page_count) VALUES (?, ?)",
            (filename, page_count),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def add_chunk(db_path: str, doc_id: int, page_num: int, text: str) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO chunks (doc_id, page_num, text) VALUES (?, ?, ?)",
            (doc_id, page_num, text),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_all_documents(db_path: str) -> list:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, filename, page_count, uploaded_at FROM documents ORDER BY uploaded_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_chunks_for_doc(db_path: str, doc_id: int) -> list:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, doc_id, page_num, text FROM chunks WHERE doc_id = ? ORDER BY page_num",
            (doc_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_chunks(db_path: str) -> list:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT c.id, c.doc_id, c.page_num, c.text, d.filename "
            "FROM chunks c JOIN documents d ON c.doc_id = d.id ORDER BY c.doc_id, c.page_num"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_document(db_path: str, doc_id: int) -> None:
    conn = _connect(db_path)
    try:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
    finally:
        conn.close()


def add_conversation(db_path: str) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute("INSERT INTO conversations DEFAULT VALUES")
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def add_message(db_path: str, conv_id: int, role: str, content: str) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO messages (conv_id, role, content) VALUES (?, ?, ?)",
            (conv_id, role, content),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_messages(db_path: str, conv_id: int) -> list:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, role, content, created_at FROM messages WHERE conv_id = ? ORDER BY created_at",
            (conv_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
