import json
import pickle

import numpy as np
import pandas as pd

from ..dao.model_dao import ModelDAO


def get_model_list() -> list[dict]:
    """Return all trained models with their metadata."""
    dao = ModelDAO()
    return dao.get_all()


def get_model_detail(model_id: int) -> dict:
    """Return full detail for a model: metrics, features, split info."""
    dao = ModelDAO()
    model = dao.get_by_id(model_id)
    if model is None:
        raise ValueError(f"模型 ID={model_id} 不存在")
    return model


def predict(model_id: int, feature_values: dict) -> float:
    """Run prediction using a trained model.

    feature_values: dict mapping feature name → value for all features the model expects.
    """
    mdl_dao = ModelDAO()
    model_record = mdl_dao.get_by_id(model_id)
    if model_record is None:
        raise ValueError(f"模型 ID={model_id} 不存在")

    meta = model_record["metadata"]
    model_type = meta.get("model_type")

    # Load feature info
    feature_info_path = meta.get("feature_info_path")
    if feature_info_path:
        with open(feature_info_path, "r", encoding="utf-8") as f:
            feature_info = json.load(f)
    else:
        feature_info = {
            "numeric_features": meta.get("numeric_features", []),
            "categorical_features": meta.get("categorical_features", []),
        }

    numeric_features = feature_info.get("numeric_features", [])
    categorical_features = feature_info.get("categorical_features", [])

    # Build a single-row DataFrame in the expected order
    all_features = numeric_features + categorical_features
    row_data = {}
    for feat in all_features:
        val = feature_values.get(feat)
        if feat in numeric_features:
            row_data[feat] = float(val) if val is not None else 0.0
        else:
            row_data[feat] = str(val) if val is not None else "Unknown"

    df = pd.DataFrame([row_data])

    if model_type == "sklearn":
        return _predict_sklearn(model_record, df)
    elif model_type == "pytorch":
        return _predict_pytorch(model_record, df)
    else:
        raise ValueError(f"不支持的模型类型: {model_type}")


def _predict_sklearn(model_record: dict, df: pd.DataFrame) -> float:
    model_path = model_record["metadata"].get("model_path")
    with open(model_path, "rb") as f:
        pipeline = pickle.load(f)
    pred = pipeline.predict(df)
    return float(pred[0])


def _predict_pytorch(model_record: dict, df: pd.DataFrame) -> float:
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        raise ImportError("PyTorch 未安装")

    meta = model_record["metadata"]

    # Load preprocessor
    preprocessor_path = meta.get("preprocessor_path")
    with open(preprocessor_path, "rb") as f:
        preprocessor = pickle.load(f)

    X = preprocessor.transform(df)

    # Load model
    model_path = meta.get("model_path")
    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
    input_dim = checkpoint["input_dim"]

    model = nn.Sequential(
        nn.Linear(input_dim, 64),
        nn.ReLU(),
        nn.Linear(64, 32),
        nn.ReLU(),
        nn.Linear(32, 1),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    X_t = torch.tensor(X, dtype=torch.float32)
    with torch.no_grad():
        pred_scaled = model(X_t).item()

    # Inverse standardization: the model was trained on (y - mean)/std
    y_mean = checkpoint.get("y_mean", 0.0)
    y_std = checkpoint.get("y_std", 1.0)
    return float(pred_scaled * y_std + y_mean)
