# app/routes.py
import os
from pathlib import Path

from flask import (
    Flask, request, redirect, url_for, render_template,
    flash, jsonify, session
)
from werkzeug.utils import secure_filename

from core.ingest import ingest_pdf
from core.retrieve import retrieve
from core.answer import answer
from db.access import (
    get_all_documents, get_all_chunks, delete_document,
    add_conversation, add_message, get_messages
)


def register(app: Flask) -> None:

    @app.route("/")
    def index():
        db_path = app.config["DB_PATH"]
        docs = get_all_documents(db_path)
        conv_id = session.get("conv_id")
        messages = get_messages(db_path, conv_id) if conv_id else []
        return render_template("index.html", docs=docs, messages=messages)

    @app.route("/upload", methods=["POST"])
    def upload():
        db_path = app.config["DB_PATH"]
        upload_dir = app.config["UPLOAD_FOLDER"]
        f = request.files.get("file")
        password = request.form.get("password", "")

        if not f or not f.filename:
            flash("No file selected.")
            return redirect(url_for("index"))

        if not f.filename.lower().endswith(".pdf"):
            flash("Only PDF files are accepted.")
            return redirect(url_for("index"))

        safe_name = secure_filename(f.filename)
        if not safe_name:
            flash("Invalid filename.")
            return redirect(url_for("index"))

        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        dest = os.path.join(upload_dir, safe_name)

        existing_docs = get_all_documents(db_path)
        if any(d["filename"] == safe_name for d in existing_docs):
            flash(f"A document named '{safe_name}' is already uploaded. Delete it first to re-upload.")
            return redirect(url_for("index"))

        f.save(dest)

        try:
            ingest_pdf(dest, safe_name, db_path, password)
            flash(f"Uploaded and indexed: {safe_name}")
        except Exception as exc:
            if "PasswordIncorrect" in repr(exc) or "PdfminerException" in type(exc).__name__:
                flash("Incorrect or missing PDF password.")
            else:
                flash(f"Could not process PDF: {type(exc).__name__}: {exc}")
            try:
                os.remove(dest)
            except OSError:
                pass

        return redirect(url_for("index"))

    @app.route("/delete/<int:doc_id>", methods=["POST"])
    def delete(doc_id):
        db_path = app.config["DB_PATH"]
        upload_dir = app.config["UPLOAD_FOLDER"]

        # Get filename before deleting from DB
        docs = get_all_documents(db_path)
        doc = next((d for d in docs if d["id"] == doc_id), None)

        delete_document(db_path, doc_id)

        if doc:
            file_path = os.path.join(upload_dir, doc["filename"])
            try:
                os.remove(file_path)
            except OSError:
                pass

        flash("Document deleted.")
        return redirect(url_for("index"))

    @app.route("/ask", methods=["POST"])
    def ask():
        db_path = app.config["DB_PATH"]
        data = request.get_json(silent=True) or {}
        question = (data.get("question") or "").strip()
        if not question:
            return jsonify({"error": "question is required"}), 400

        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            return jsonify({"error": "GROQ_API_KEY environment variable is not set"}), 503
        chunks = get_all_chunks(db_path)
        top_chunks = retrieve(question, chunks, top_k=5)
        result = answer(question, top_chunks, api_key)

        conv_id = session.get("conv_id")
        if conv_id is None:
            conv_id = add_conversation(db_path)
            session["conv_id"] = conv_id
        add_message(db_path, conv_id, "user", question)
        add_message(db_path, conv_id, "assistant", result)

        return jsonify({"answer": result})

    @app.route("/history")
    def history():
        db_path = app.config["DB_PATH"]
        conv_id = session.get("conv_id")
        messages = get_messages(db_path, conv_id) if conv_id else []
        return jsonify([{"role": m["role"], "content": m["content"]} for m in messages])
