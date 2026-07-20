import os
import secrets

from flask import Flask

def create_app(db_path: str = "data/fin_rag.db") -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path
    app.config["UPLOAD_FOLDER"] = "data/uploads"
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB limit
    app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

    from db.access import init_db
    from pathlib import Path
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    init_db(db_path)

    from app import routes
    routes.register(app)

    return app
