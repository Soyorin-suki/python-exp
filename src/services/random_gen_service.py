"""Generate synthetic datasets for testing the prediction pipeline."""

import numpy as np
import pandas as pd

from ..dao import RAW_DIR, ensure_data_dirs
from ..dao.dataset_dao import DatasetDAO


def generate_and_save(gen_type: str, n_samples: int, noise: float, filename: str) -> str:
    """Generate synthetic data, save CSV to raw dir, create DB record.  Returns filename."""
    ensure_data_dirs()

    dao = DatasetDAO()
    if dao.filename_exists(filename):
        raise FileExistsError(f"文件 {filename} 已存在，请重命名后重新上传")

    rng = np.random.default_rng(42)

    if gen_type == "linear":
        # y = 3.5 * x1 + 2.0 * x2 - 1.2 * x3 + 0.5 * x4 + noise
        x1 = rng.uniform(0, 100, n_samples)
        x2 = rng.uniform(-10, 10, n_samples)
        x3 = rng.normal(50, 15, n_samples)
        x4 = rng.integers(0, 5, n_samples).astype(float)
        y = 3.5 * x1 + 2.0 * x2 - 1.2 * x3 + 0.5 * x4 + rng.normal(0, noise * 100, n_samples)

        df = pd.DataFrame({
            "feature_1": x1,
            "feature_2": x2,
            "feature_3": x3,
            "feature_4": x4,
            "Price (in rupees)": y,
        })

    elif gen_type == "polynomial":
        # y = 0.01 * x² + 0.5 * x + 10 + noise
        x1 = rng.uniform(-50, 50, n_samples)
        x2 = rng.uniform(0, 200, n_samples)
        x3 = rng.normal(0, 10, n_samples)
        category = rng.choice(["A", "B", "C"], n_samples)
        y = 0.01 * x1**2 + 0.5 * x2 + 10 + rng.normal(0, noise * 50, n_samples)

        df = pd.DataFrame({
            "feature_1": x1,
            "feature_2": x2,
            "feature_3": x3,
            "category": category,
            "Price (in rupees)": y,
        })

    else:
        raise ValueError(f"不支持的生成类型: {gen_type}")

    file_path = RAW_DIR / filename
    df.to_csv(file_path, index=False)

    dao.insert(
        filename=filename,
        metadata={
            "file_type": "csv",
            "file_path": str(file_path.resolve()),
            "is_cleaned": False,
            "clean_type": None,
            "generated": True,
            "gen_type": gen_type,
            "n_samples": n_samples,
            "noise": noise,
        },
    )
    return filename
