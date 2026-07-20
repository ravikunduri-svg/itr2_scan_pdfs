from flask import Flask

def create_app(db_path: str = "data/fin_rag.db") -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path
    app.config["UPLOAD_FOLDER"] = "data/uploads"
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB limit
    app.secret_key = "dev-secret-change-in-prod"

    from app import routes
    routes.register(app)

    return app
