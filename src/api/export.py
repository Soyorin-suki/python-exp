import io
import os
import zipfile
from pathlib import Path

from flask import Blueprint, render_template, send_file

from ..dao.dataset_dao import DatasetDAO
from ..dao.model_dao import ModelDAO

bp = Blueprint("export", __name__)


@bp.route("/export")
def export_view():
    ds_dao = DatasetDAO()
    mdl_dao = ModelDAO()

    # Separate raw and cleaned datasets
    all_datasets = ds_dao.get_all()
    raw_datasets = [d for d in all_datasets if not d["metadata"].get("is_cleaned")]
    cleaned_datasets = [d for d in all_datasets if d["metadata"].get("is_cleaned")]
    models = mdl_dao.get_all()

    # Enrich models with companion file info
    for m in models:
        meta = m["metadata"]
        m["has_features_json"] = bool(
            meta.get("feature_info_path")
            and Path(meta["feature_info_path"]).exists()
        )
        m["has_preprocessor"] = bool(
            meta.get("preprocessor_path")
            and Path(meta["preprocessor_path"]).exists()
        )

    return render_template(
        "export.html",
        raw_datasets=raw_datasets,
        cleaned_datasets=cleaned_datasets,
        models=models,
    )


# ── Dataset downloads ──────────────────────────────────────────────

@bp.route("/export/download/dataset/<int:dataset_id>")
def download_dataset(dataset_id: int):
    dao = DatasetDAO()
    record = dao.get_by_id(dataset_id)
    if record is None:
        return "数据集不存在", 404

    file_path = Path(record["metadata"].get("file_path", ""))
    if not file_path.exists():
        return "文件不存在，可能已被移动或删除", 404

    download_name = record["filename"]
    return send_file(
        str(file_path.resolve()),
        as_attachment=True,
        download_name=download_name,
    )


# ── Model downloads ─────────────────────────────────────────────────

@bp.route("/export/download/model/<int:model_id>")
def download_model(model_id: int):
    """Download the model file (.pkl or .pt)."""
    dao = ModelDAO()
    record = dao.get_by_id(model_id)
    if record is None:
        return "模型不存在", 404

    file_path = Path(record["metadata"].get("model_path", ""))
    if not file_path.exists():
        return "模型文件不存在", 404

    download_name = Path(file_path).name
    return send_file(
        str(file_path.resolve()),
        as_attachment=True,
        download_name=download_name,
    )


@bp.route("/export/download/model/<int:model_id>/features")
def download_model_features(model_id: int):
    """Download the features.json for a model."""
    dao = ModelDAO()
    record = dao.get_by_id(model_id)
    if record is None:
        return "模型不存在", 404

    file_path = Path(record["metadata"].get("feature_info_path", ""))
    if not file_path.exists():
        return "特征文件不存在", 404

    download_name = f"{record['model_name'].rsplit('.', 1)[0]}.features.json"
    return send_file(
        str(file_path.resolve()),
        as_attachment=True,
        download_name=download_name,
        mimetype="application/json",
    )


@bp.route("/export/download/model/<int:model_id>/preprocessor")
def download_model_preprocessor(model_id: int):
    """Download the preprocessor.pkl for a pytorch model."""
    dao = ModelDAO()
    record = dao.get_by_id(model_id)
    if record is None:
        return "模型不存在", 404

    file_path = Path(record["metadata"].get("preprocessor_path", ""))
    if not file_path.exists():
        return "预处理器文件不存在", 404

    download_name = f"{record['model_name'].rsplit('.', 1)[0]}.preprocessor.pkl"
    return send_file(
        str(file_path.resolve()),
        as_attachment=True,
        download_name=download_name,
        mimetype="application/octet-stream",
    )


@bp.route("/export/download/model/<int:model_id>/bundle")
def download_model_bundle(model_id: int):
    """Download model + features.json + preprocessor (if exists) as a zip."""
    dao = ModelDAO()
    record = dao.get_by_id(model_id)
    if record is None:
        return "模型不存在", 404

    meta = record["metadata"]
    model_path = Path(meta.get("model_path", ""))
    feature_path = Path(meta.get("feature_info_path", ""))
    preprocessor_path = Path(meta.get("preprocessor_path", ""))

    if not model_path.exists():
        return "模型文件不存在", 404

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(model_path, model_path.name)
        if feature_path.exists():
            zf.write(feature_path, feature_path.name)
        if preprocessor_path.exists():
            zf.write(preprocessor_path, preprocessor_path.name)

    buf.seek(0)
    base = record["model_name"].rsplit(".", 1)[0]
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"{base}_bundle.zip",
        mimetype="application/zip",
    )
