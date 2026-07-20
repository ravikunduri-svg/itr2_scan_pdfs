import pdfplumber
from db.access import add_document, add_chunk, delete_document


def extract_pages(pdf_path: str, password: str = "") -> list:
    """Extract text per page. Returns [{page_num, text}], blank pages excluded."""
    result = []
    with pdfplumber.open(pdf_path, password=password or None) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                result.append({"page_num": i, "text": text})
    return result


def ingest_pdf(pdf_path: str, filename: str, db_path: str, password: str = "") -> int:
    """Extract text from pdf_path, store as document + chunks in DB. Returns doc_id."""
    pages = extract_pages(pdf_path, password)
    doc_id = add_document(db_path, filename, len(pages))
    try:
        for page in pages:
            add_chunk(db_path, doc_id, page["page_num"], page["text"])
    except Exception:
        delete_document(db_path, doc_id)
        raise
    return doc_id
