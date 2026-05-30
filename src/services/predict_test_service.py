"""Random data prediction test — generate test points and visualize model fit."""

import base64
import io
import json
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..dao.dataset_dao import DatasetDAO
from ..dao.model_dao import ModelDAO

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def get_testable_features(model_id: int) -> dict:
    """Return feature info for prediction testing: numeric features only."""
    mdl_dao = ModelDAO()
    model_record = mdl_dao.get_by_id(model_id)
    if model_record is None:
        raise ValueError(f"模型 ID={model_id} 不存在")

    meta = model_record["metadata"]
    feature_info_path = meta.get("feature_info_path")
    if feature_info_path:
        with open(feature_info_path, "r", encoding="utf-8") as f:
            fi = json.load(f)
    else:
        fi = {"numeric_features": meta.get("numeric_features", []),
              "categorical_features": meta.get("categorical_features", [])}

    return {
        "model_name": model_record["model_name"],
        "model_type": meta.get("model_type"),
        "numeric_features": fi.get("numeric_features", []),
        "categorical_features": fi.get("categorical_features", []),
        "train_data_id": meta.get("train_data_id"),
    }


def run_prediction_test(
    model_id: int,
    feature_name: str,
    n_points: int = 80,
) -> str:
    """Generate random test points for one numeric feature, predict, and plot.

    Returns base64 PNG with:
      - Scatter: original training data points (feature vs target)
      - Line: model predictions across generated random points (sorted)
    """
    rng = np.random.default_rng(42)

    # 1. Load model info
    info = get_testable_features(model_id)

    # 2. Load original training dataset
    ds_dao = DatasetDAO()
    ds_record = ds_dao.get_by_id(info["train_data_id"])
    if ds_record is None:
        raise ValueError("训练数据集不存在")

    df = pd.read_csv(ds_record["metadata"]["file_path"])
    target = "Price (in rupees)"

    # 3. Load the trained model
    mdl_dao = ModelDAO()
    model_record = mdl_dao.get_by_id(model_id)
    model_type = model_record["metadata"]["model_type"]

    if model_type == "sklearn":
        with open(model_record["metadata"]["model_path"], "rb") as f:
            pipeline = pickle.load(f)
    elif model_type == "pytorch":
        # For pytorch, load preprocessor + model
        with open(model_record["metadata"]["preprocessor_path"], "rb") as f:
            preprocessor = pickle.load(f)
        import torch
        import torch.nn as nn
        checkpoint = torch.load(
            model_record["metadata"]["model_path"], map_location="cpu", weights_only=False
        )
        input_dim = checkpoint["input_dim"]
        torch_model = nn.Sequential(
            nn.Linear(input_dim, 64), nn.ReLU(),
            nn.Linear(64, 32), nn.ReLU(),
            nn.Linear(32, 1),
        )
        torch_model.load_state_dict(checkpoint["model_state_dict"])
        torch_model.eval()
    else:
        raise ValueError(f"不支持的模型类型: {model_type}")

    # 4. Build baseline row (means for numeric, modes for categorical)
    baseline = {}
    for col in info["numeric_features"]:
        if col == feature_name:
            continue
        if col in df.columns:
            baseline[col] = df[col].mean()

    for col in info["categorical_features"]:
        if col in df.columns:
            baseline[col] = df[col].mode()[0] if len(df[col].mode()) > 0 else "Unknown"

    # 5. Generate random test values for the selected feature (normal distribution)
    if feature_name in df.columns:
        feat_mean = df[feature_name].mean()
        feat_std = df[feature_name].std()
    else:
        feat_mean = 0
        feat_std = 1

    # Handle edge cases: zero std or NaN
    if pd.isna(feat_std) or feat_std == 0:
        feat_std = abs(feat_mean) * 0.2 if feat_mean != 0 else 1.0

    random_vals = rng.normal(feat_mean, feat_std, n_points)

    # Also generate a smooth sorted range for the line
    sorted_min = float(df[feature_name].min())
    sorted_max = float(df[feature_name].max())
    sorted_range = np.linspace(sorted_min, sorted_max, n_points)

    # 6. Build DataFrames and predict
    all_features = info["numeric_features"] + info["categorical_features"]

    # For scatter (random points)
    random_rows = []
    for val in random_vals:
        row = {}
        for feat in all_features:
            if feat == feature_name:
                row[feat] = val
            elif feat in baseline:
                row[feat] = baseline[feat]
            else:
                row[feat] = 0 if feat in info["numeric_features"] else "Unknown"
        random_rows.append(row)
    random_df = pd.DataFrame(random_rows)

    # For line (sorted range)
    sorted_rows = []
    for val in sorted_range:
        row = {}
        for feat in all_features:
            if feat == feature_name:
                row[feat] = val
            elif feat in baseline:
                row[feat] = baseline[feat]
            else:
                row[feat] = 0 if feat in info["numeric_features"] else "Unknown"
        sorted_rows.append(row)
    sorted_df = pd.DataFrame(sorted_rows)

    # 7. Run predictions
    if model_type == "sklearn":
        pred_random = pipeline.predict(random_df)
        pred_sorted = pipeline.predict(sorted_df)
    else:
        X_random = preprocessor.transform(random_df)
        X_sorted = preprocessor.transform(sorted_df)
        with torch.no_grad():
            pred_random = torch_model(torch.tensor(X_random, dtype=torch.float32)).numpy().flatten()
            pred_sorted = torch_model(torch.tensor(X_sorted, dtype=torch.float32)).numpy().flatten()

    # 8. Plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Original data scatter (sample up to 3000 points to keep performance)
    sample_n = min(3000, len(df))
    df_sample = df.sample(n=sample_n, random_state=42) if len(df) > sample_n else df
    ax.scatter(
        df_sample[feature_name], df_sample[target],
        alpha=0.25, s=8, color="#4a90d9", label="原始数据"
    )

    # Prediction line (sorted)
    ax.plot(
        sorted_range, pred_sorted,
        color="#e8743e", linewidth=2.5, label="模型预测线"
    )

    ax.set_xlabel(feature_name)
    ax.set_ylabel(target)
    ax.set_title(f"模型预测测试 — {feature_name} vs {target}\n({info['model_name']}, {info['model_type']})")
    ax.legend()
    ax.grid(True, alpha=0.3)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)

    return b64
