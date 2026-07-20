from pathlib import Path
from app import create_app
from db.access import init_db

DB_PATH = "data/fin_rag.db"

app = create_app(DB_PATH)

if __name__ == "__main__":
    Path("data/uploads").mkdir(parents=True, exist_ok=True)
    init_db(DB_PATH)
    app.run(host="127.0.0.1", port=5001, debug=True)
