import re

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from ..dao import CLEANED_DIR, RAW_DIR, ensure_data_dirs
from ..dao.dataset_dao import DatasetDAO

TARGET_COLUMN = "Price (in rupees)"


def _parse_amount(val) -> float:
    """Parse '42 Lac' → 4_200_000, '1.40 Cr' → 14_000_000."""
    if pd.isna(val) or not isinstance(val, str):
        return np.nan
    val = val.strip().lower()
    val = val.replace(",", "").strip()
    match = re.match(r"^([\d.]+)\s*(lac|cr)$", val)
    if not match:
        return np.nan
    num = float(match.group(1))
    unit = match.group(2)
    if unit == "lac":
        return num * 100_000
    elif unit == "cr":
        return num * 10_000_000
    return np.nan


def _parse_area(val) -> float:
    """Parse '500 sqft' → 500, '1200 sqft' → 1200."""
    if pd.isna(val) or not isinstance(val, str):
        return np.nan
    val = val.strip().lower()
    match = re.match(r"^([\d.]+)\s*sqft", val)
    if not match:
        return np.nan
    return float(match.group(1))


def _parse_bathroom(val) -> float | None:
    """Parse bathroom values, return numeric or NaN."""
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return np.nan


def load_raw_dataset(dataset_id: int) -> tuple[pd.DataFrame, dict]:
    """Load a raw dataset from disk by its DB id. Returns (df, db_record)."""
    dao = DatasetDAO()
    record = dao.get_by_id(dataset_id)
    if record is None:
        raise ValueError(f"数据集 ID={dataset_id} 不存在")

    file_path = record["metadata"].get("file_path")
    file_type = record["metadata"].get("file_type", "csv")

    if file_type == "csv":
        df = pd.read_csv(file_path)
    elif file_type == "xlsx":
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")

    return df, record


def clean_dataset(
    dataset_id: int,
    fill_missing: bool = True,
    remove_outliers: bool = True,
    normalize: bool = True,
) -> str:
    """Apply cleaning ops to a raw dataset, save to cleaned dir, update DB.

    Returns the cleaned filename.
    """
    ensure_data_dirs()
    df, record = load_raw_dataset(dataset_id)
    filename = record["filename"]
    # Use same filename, just in the cleaned dir
    cleaned_path = CLEANED_DIR / filename

    # Drop rows where target is missing (can't use for training)
    if TARGET_COLUMN in df.columns:
        df = df.dropna(subset=[TARGET_COLUMN])

    # Drop columns that are entirely NaN
    df = df.dropna(axis=1, how="all")

    # Parse structured columns into numeric
    if "Amount(in rupees)" in df.columns:
        df["Amount(in rupees)"] = pd.to_numeric(
            df["Amount(in rupees)"].apply(_parse_amount), errors="coerce"
        )

    if "Carpet Area" in df.columns:
        df["Carpet Area"] = pd.to_numeric(
            df["Carpet Area"].apply(_parse_area), errors="coerce"
        )

    if "Super Area" in df.columns:
        df["Super Area"] = pd.to_numeric(
            df["Super Area"].apply(_parse_area), errors="coerce"
        )

    if "Bathroom" in df.columns:
        df["Bathroom"] = pd.to_numeric(
            df["Bathroom"].apply(_parse_bathroom), errors="coerce"
        )

    if "Balcony" in df.columns:
        df["Balcony"] = pd.to_numeric(
            df["Balcony"].apply(_parse_bathroom), errors="coerce"
        )

    # Separate numeric and categorical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

    if fill_missing:
        # Fill numeric with median
        for col in numeric_cols:
            if df[col].isna().any():
                df[col] = df[col].fillna(df[col].median())
        # Fill categorical with mode
        for col in categorical_cols:
            if df[col].isna().any():
                mode_vals = df[col].mode()
                fill_val = mode_vals[0] if len(mode_vals) > 0 else "Unknown"
                df[col] = df[col].fillna(fill_val)

    if remove_outliers:
        # IQR method for numeric columns (except target)
        for col in numeric_cols:
            if col == TARGET_COLUMN:
                continue
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            if IQR > 0:
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                df = df[(df[col] >= lower) & (df[col] <= upper)]

    if normalize:
        scaler = StandardScaler()
        cols_to_scale = [c for c in numeric_cols if c != TARGET_COLUMN and df[c].notna().all()]
        if cols_to_scale:
            df[cols_to_scale] = scaler.fit_transform(df[cols_to_scale])

    # Save cleaned dataset
    file_type = record["metadata"].get("file_type", "csv")
    if file_type == "csv":
        df.to_csv(cleaned_path, index=False)
    else:
        df.to_excel(cleaned_path, index=False)

    # Update DB record
    dao = DatasetDAO()
    metadata = record["metadata"]
    metadata["is_cleaned"] = True
    metadata["clean_type"] = _build_clean_type(fill_missing, remove_outliers, normalize)
    metadata["file_path"] = str(cleaned_path.resolve())
    metadata["columns"] = df.columns.tolist()
    metadata["numeric_columns"] = [c for c in numeric_cols if c in df.columns]
    metadata["categorical_columns"] = [c for c in categorical_cols if c in df.columns]
    metadata["row_count"] = len(df)
    dao.update_metadata(dataset_id, metadata)

    return filename


def _build_clean_type(fill_missing: bool, remove_outliers: bool, normalize: bool) -> str:
    parts = []
    if fill_missing:
        parts.append("缺失值填充")
    if remove_outliers:
        parts.append("异常值处理")
    if normalize:
        parts.append("数据标准化")
    return ",".join(parts) if parts else "none"


def get_dataset_features(dataset_id: int) -> dict:
    """Return feature metadata for a dataset (numeric + categorical columns, types)."""
    df, record = load_raw_dataset(dataset_id)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

    return {
        "filename": record["filename"],
        "target": TARGET_COLUMN if TARGET_COLUMN in df.columns else None,
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "total_features": len(numeric_cols) + len(categorical_cols),
    }
