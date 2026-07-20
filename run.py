from app import create_app

DB_PATH = "data/fin_rag.db"

app = create_app(DB_PATH)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
