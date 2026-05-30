import json
from . import get_db, init_db


class ModelDAO:
    """CRUD for models table. Metadata is stored as JSON in the metadata column."""

    def __init__(self):
        init_db()

    def insert(self, model_name: str, metadata: dict) -> int:
        conn = get_db()
        c = conn.execute(
            "INSERT INTO models (model_name, metadata) VALUES (?, ?)",
            (model_name, json.dumps(metadata, ensure_ascii=False)),
        )
        conn.commit()
        row_id = c.lastrowid
        conn.close()
        return row_id

    def get_all(self) -> list[dict]:
        conn = get_db()
        rows = conn.execute(
            "SELECT id, model_name, metadata FROM models ORDER BY id DESC"
        ).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]

    def get_by_id(self, model_id: int) -> dict | None:
        conn = get_db()
        row = conn.execute(
            "SELECT id, model_name, metadata FROM models WHERE id = ?", (model_id,)
        ).fetchone()
        conn.close()
        return _row_to_dict(row) if row else None


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "model_name": row["model_name"],
        "metadata": json.loads(row["metadata"]),
    }
