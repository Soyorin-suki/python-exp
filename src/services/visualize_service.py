import base64
import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..dao.dataset_dao import DatasetDAO

# Chinese-capable font setup
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
TARGET_COLUMN = "Price (in rupees)"


def _load_data(dataset_id: int) -> tuple[pd.DataFrame, dict]:
    dao = DatasetDAO()
    record = dao.get_by_id(dataset_id)
    if record is None:
        raise ValueError(f"数据集 ID={dataset_id} 不存在")

    file_path = record["metadata"].get("file_path")
    file_type = record["metadata"].get("file_type", "csv")
    df = pd.read_csv(file_path) if file_type == "csv" else pd.read_excel(file_path)
    return df, record


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return b64


def generate_histogram(dataset_id: int, column: str) -> str:
    """Generate a histogram for a numeric column. Returns base64 PNG."""
    df, _ = _load_data(dataset_id)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if column not in numeric_cols:
        raise ValueError(f"列 '{column}' 不是数值类型或不存在")

    series = df[column].dropna()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(series, bins=30, color="#4a90d9", edgecolor="white", alpha=0.85)
    ax.set_title(f"{column} 分布直方图")
    ax.set_xlabel(column)
    ax.set_ylabel("频数")
    return _fig_to_base64(fig)


def generate_scatter(dataset_id: int, x_col: str, y_col: str) -> str:
    """Generate a scatter plot of two numeric columns. Returns base64 PNG."""
    df, _ = _load_data(dataset_id)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in [x_col, y_col]:
        if col not in numeric_cols:
            raise ValueError(f"列 '{col}' 不是数值类型或不存在")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df[x_col], df[y_col], alpha=0.3, s=5, color="#e8743e")
    ax.set_title(f"{x_col} vs {y_col}")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    return _fig_to_base64(fig)


def generate_correlation_heatmap(dataset_id: int) -> str:
    """Generate a correlation heatmap for numeric columns. Returns base64 PNG."""
    df, _ = _load_data(dataset_id)

    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        raise ValueError("数值列不足，无法生成相关性热力图")

    corr = numeric_df.corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(corr.columns, fontsize=8)
    ax.set_title("数值特征相关性热力图")
    plt.colorbar(im, ax=ax, shrink=0.8)
    return _fig_to_base64(fig)


def get_available_charts(dataset_id: int) -> dict:
    """Return available chart options for a dataset."""
    df, record = _load_data(dataset_id)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

    return {
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "chart_types": [
            {"key": "histogram", "name": "直方图", "needs": "single_numeric"},
            {"key": "scatter", "name": "散点图", "needs": "two_numeric"},
            {"key": "correlation", "name": "相关性热力图", "needs": "none"},
        ],
    }
