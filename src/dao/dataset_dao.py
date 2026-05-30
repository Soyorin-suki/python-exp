import json
from . import get_db, init_db


class DatasetDAO:
    """CRUD for datasets table. Metadata is stored as JSON in the metadata column."""

    def __init__(self):
        init_db()

    def insert(self, filename: str, metadata: dict) -> int:
        conn = get_db()
        c = conn.execute(
            "INSERT INTO datasets (filename, metadata) VALUES (?, ?)",
            (filename, json.dumps(metadata, ensure_ascii=False)),
        )
        conn.commit()
        row_id = c.lastrowid
        conn.close()
        return row_id

    def get_all(self) -> list[dict]:
        conn = get_db()
        rows = conn.execute(
            "SELECT id, filename, metadata FROM datasets ORDER BY id DESC"
        ).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]

    def get_by_id(self, dataset_id: int) -> dict | None:
        conn = get_db()
        row = conn.execute(
            "SELECT id, filename, metadata FROM datasets WHERE id = ?", (dataset_id,)
        ).fetchone()
        conn.close()
        return _row_to_dict(row) if row else None

    def get_by_filename(self, filename: str) -> dict | None:
        conn = get_db()
        row = conn.execute(
            "SELECT id, filename, metadata FROM datasets WHERE filename = ?",
            (filename,),
        ).fetchone()
        conn.close()
        return _row_to_dict(row) if row else None

    def get_raw_datasets(self) -> list[dict]:
        """Return datasets where is_cleaned is false."""
        conn = get_db()
        rows = conn.execute(
            "SELECT id, filename, metadata FROM datasets ORDER BY id DESC"
        ).fetchall()
        conn.close()
        return [r for r in (_row_to_dict(r) for r in rows) if not r["metadata"].get("is_cleaned")]

    def get_cleaned_datasets(self) -> list[dict]:
        """Return datasets where is_cleaned is true."""
        conn = get_db()
        rows = conn.execute(
            "SELECT id, filename, metadata FROM datasets ORDER BY id DESC"
        ).fetchall()
        conn.close()
        return [r for r in (_row_to_dict(r) for r in rows) if r["metadata"].get("is_cleaned")]

    def update_metadata(self, dataset_id: int, metadata: dict) -> None:
        conn = get_db()
        conn.execute(
            "UPDATE datasets SET metadata = ? WHERE id = ?",
            (json.dumps(metadata, ensure_ascii=False), dataset_id),
        )
        conn.commit()
        conn.close()

    def update_filename(self, dataset_id: int, filename: str) -> None:
        conn = get_db()
        conn.execute(
            "UPDATE datasets SET filename = ? WHERE id = ?", (filename, dataset_id)
        )
        conn.commit()
        conn.close()

    def filename_exists(self, filename: str) -> bool:
        conn = get_db()
        row = conn.execute(
            "SELECT 1 FROM datasets WHERE filename = ?", (filename,)
        ).fetchone()
        conn.close()
        return row is not None


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "filename": row["filename"],
        "metadata": json.loads(row["metadata"]),
    }
