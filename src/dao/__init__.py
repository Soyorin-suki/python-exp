import sqlite3
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_DIR = PROJECT_ROOT / "data" / "database"
DB_PATH = DB_DIR / "app.db"

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "datasets" / "raw"
CLEANED_DIR = DATA_DIR / "datasets" / "cleaned"
MODELS_DIR = DATA_DIR / "models"


def get_db():
    """Return a connection to the SQLite database, creating dirs as needed."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            metadata TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            metadata TEXT NOT NULL DEFAULT '{}'
        );
    """)
    conn.commit()
    conn.close()


def ensure_data_dirs():
    """Create all data subdirectories if they don't exist."""
    for d in [RAW_DIR, CLEANED_DIR, MODELS_DIR, DB_DIR]:
        d.mkdir(parents=True, exist_ok=True)
