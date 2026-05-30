import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ..dao import CLEANED_DIR, MODELS_DIR, ensure_data_dirs
from ..dao.dataset_dao import DatasetDAO
from ..dao.model_dao import ModelDAO

TARGET_COLUMN = "Price (in rupees)"


# Columns that are free-text and should never be used as categorical features
TEXT_COLUMNS = {"Title", "Description"}

# Drop categorical columns with more unique values than this threshold
MAX_CATEGORY_UNIQUE = 500


def _build_preprocessor(df: pd.DataFrame) -> ColumnTransformer:
    """Build a ColumnTransformer for numeric + categorical features.

    Filters out:
      - Free-text columns (Title, Description)
      - Categorical columns with > MAX_CATEGORY_UNIQUE unique values
      - Categorical columns with only 1 unique value (no variance)
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    raw_categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

    # Remove target from numeric if present
    if TARGET_COLUMN in numeric_cols:
        numeric_cols.remove(TARGET_COLUMN)

    # Filter categorical columns
    categorical_cols = []
    dropped_cols = []
    for col in raw_categorical_cols:
        if col in TEXT_COLUMNS:
            dropped_cols.append(f"{col} (text column)")
            continue
        n_unique = df[col].nunique()
        if n_unique <= 1:
            dropped_cols.append(f"{col} (only 1 unique value)")
            continue
        if n_unique > MAX_CATEGORY_UNIQUE:
            dropped_cols.append(f"{col} ({n_unique} unique > {MAX_CATEGORY_UNIQUE})")
            continue
        categorical_cols.append(col)

    if dropped_cols:
        print(f"[_build_preprocessor] Dropped columns: {', '.join(dropped_cols)}")

    # Cast all categorical columns to string — prevents OneHotEncoder
    # failures when a column has mixed types (e.g. int + str from
    # pandas chunked CSV parsing with low_memory=True).
    for col in categorical_cols:
        df[col] = df[col].astype(str)

    transformers = []
    if numeric_cols:
        transformers.append(("num", StandardScaler(), numeric_cols))
    if categorical_cols:
        transformers.append(
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols)
        )

    return ColumnTransformer(transformers, remainder="drop"), numeric_cols, categorical_cols


def train_sklearn(dataset_id: int, test_size: float = 0.2, random_state: int = 42) -> dict:
    """Train a sklearn LinearRegression model. Save model and return metrics."""
    ensure_data_dirs()

    # Load cleaned dataset
    ds_dao = DatasetDAO()
    record = ds_dao.get_by_id(dataset_id)
    if record is None:
        raise ValueError(f"数据集 ID={dataset_id} 不存在")
    if not record["metadata"].get("is_cleaned"):
        raise ValueError("请先清洗数据集再训练")

    file_path = record["metadata"].get("file_path")
    file_type = record["metadata"].get("file_type", "csv")

    if file_type == "csv":
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"数据集中没有目标列: {TARGET_COLUMN}")

    # Drop rows where target is NaN
    df = df.dropna(subset=[TARGET_COLUMN])

    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    # Build preprocessor
    preprocessor, numeric_cols, categorical_cols = _build_preprocessor(df)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Build and train pipeline
    model = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", LinearRegression()),
    ])
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = float(np.sqrt(mse))
    r2 = r2_score(y_test, y_pred)

    # Save model
    model_name = f"{record['filename'].rsplit('.', 1)[0]}_sklearn_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pkl"
    model_path = MODELS_DIR / model_name
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    # Save feature info alongside model
    feature_info_path = MODELS_DIR / f"{model_name}.features.json"
    feature_info = {
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "target": TARGET_COLUMN,
        "test_size": test_size,
        "random_state": random_state,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
    }
    with open(feature_info_path, "w", encoding="utf-8") as f:
        json.dump(feature_info, f, ensure_ascii=False, indent=2)

    # Record in DB
    mdl_dao = ModelDAO()
    mdl_dao.insert(
        model_name=model_name,
        metadata={
            "model_type": "sklearn",
            "model_path": str(model_path.resolve()),
            "feature_info_path": str(feature_info_path.resolve()),
            "train_data_id": dataset_id,
            "mse": mse,
            "rmse": rmse,
            "r2": r2,
            "test_rows": len(y_test),
            "train_rows": len(y_train),
        },
    )

    return {
        "model_name": model_name,
        "mse": mse,
        "rmse": rmse,
        "r2": r2,
        "train_rows": len(y_train),
        "test_rows": len(y_test),
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
    }


def train_pytorch(dataset_id: int, test_size: float = 0.2, random_state: int = 42,
                   epochs: int = 100, lr: float = 0.001) -> dict:
    """Train a simple feedforward NN with PyTorch. Save model and return metrics."""
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
    except ImportError:
        raise ImportError("PyTorch 未安装，请运行: uv add torch && uv sync")

    ensure_data_dirs()

    ds_dao = DatasetDAO()
    record = ds_dao.get_by_id(dataset_id)
    if record is None:
        raise ValueError(f"数据集 ID={dataset_id} 不存在")
    if not record["metadata"].get("is_cleaned"):
        raise ValueError("请先清洗数据集再训练")

    file_path = record["metadata"].get("file_path")
    file_type = record["metadata"].get("file_type", "csv")

    if file_type == "csv":
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"数据集中没有目标列: {TARGET_COLUMN}")

    df = df.dropna(subset=[TARGET_COLUMN])

    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    # Build preprocessor and transform
    preprocessor, numeric_cols, categorical_cols = _build_preprocessor(df)
    X_processed = preprocessor.fit_transform(X)
    y_vals = y.values.astype(np.float32).reshape(-1, 1)

    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y_vals, test_size=test_size, random_state=random_state
    )

    # Convert to tensors
    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.float32)
    X_test_t = torch.tensor(X_test, dtype=torch.float32)
    y_test_t = torch.tensor(y_test, dtype=torch.float32)

    # Define model
    input_dim = X_train.shape[1]
    model = nn.Sequential(
        nn.Linear(input_dim, 64),
        nn.ReLU(),
        nn.Linear(64, 32),
        nn.ReLU(),
        nn.Linear(32, 1),
    )

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    # Train
    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_train_t)
        loss = criterion(outputs, y_train_t)
        loss.backward()
        optimizer.step()

    # Evaluate
    model.eval()
    with torch.no_grad():
        y_pred_t = model(X_test_t)
        test_loss = criterion(y_pred_t, y_test_t).item()
        y_pred_np = y_pred_t.numpy().flatten()
        y_test_np = y_test_t.numpy().flatten()
        mse = mean_squared_error(y_test_np, y_pred_np)
        rmse = float(np.sqrt(mse))
        r2 = r2_score(y_test_np, y_pred_np)

    # Save model + preprocessor
    model_name = f"{record['filename'].rsplit('.',1)[0]}_pytorch_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pt"
    model_path = MODELS_DIR / model_name
    torch.save({
        "model_state_dict": model.state_dict(),
        "input_dim": input_dim,
        "architecture": "Linear(64)→ReLU→Linear(32)→ReLU→Linear(1)",
    }, model_path)

    # Save preprocessor
    preprocessor_path = MODELS_DIR / f"{model_name}.preprocessor.pkl"
    with open(preprocessor_path, "wb") as f:
        pickle.dump(preprocessor, f)

    feature_info_path = MODELS_DIR / f"{model_name}.features.json"
    feature_info = {
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "target": TARGET_COLUMN,
        "test_size": test_size,
        "random_state": random_state,
        "epochs": epochs,
        "lr": lr,
        "train_rows": len(X_train),
        "test_rows": len(y_test),
    }
    with open(feature_info_path, "w", encoding="utf-8") as f:
        json.dump(feature_info, f, ensure_ascii=False, indent=2)

    mdl_dao = ModelDAO()
    mdl_dao.insert(
        model_name=model_name,
        metadata={
            "model_type": "pytorch",
            "model_path": str(model_path.resolve()),
            "preprocessor_path": str(preprocessor_path.resolve()),
            "feature_info_path": str(feature_info_path.resolve()),
            "train_data_id": dataset_id,
            "mse": float(mse),
            "rmse": rmse,
            "r2": r2,
            "test_rows": len(y_test),
            "train_rows": len(y_train),
            "epochs": epochs,
            "lr": lr,
        },
    )

    return {
        "model_name": model_name,
        "mse": float(mse),
        "rmse": rmse,
        "r2": r2,
        "train_rows": len(y_train),
        "test_rows": len(y_test),
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
    }
