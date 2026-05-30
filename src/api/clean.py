from flask import Blueprint, request, render_template

from ..dao.dataset_dao import DatasetDAO
from ..services.clean_service import clean_dataset, get_dataset_features

bp = Blueprint("clean", __name__)


@bp.route("/clean", methods=["GET", "POST"])
def clean_view():
    msg = None
    color = "green"
    features = None

    dao = DatasetDAO()
    raw_datasets = dao.get_raw_datasets()
    cleaned_datasets = dao.get_cleaned_datasets()

    if request.method == "POST":
        dataset_id = request.form.get("dataset_id", type=int)
        fill_missing = request.form.get("fill_missing") == "1"
        remove_outliers = request.form.get("remove_outliers") == "1"
        normalize = request.form.get("normalize") == "1"

        if not dataset_id:
            msg = "请选择数据集"
            color = "red"
        else:
            try:
                filename = clean_dataset(dataset_id, fill_missing, remove_outliers, normalize)
                msg = f"数据集 {filename} 清洗完成"
                color = "green"
                features = get_dataset_features(dataset_id)
                # Refresh lists
                raw_datasets = dao.get_raw_datasets()
                cleaned_datasets = dao.get_cleaned_datasets()
            except Exception as e:
                msg = f"清洗失败: {e}"
                color = "red"

    return render_template(
        "clean.html",
        msg=msg,
        color=color,
        raw_datasets=raw_datasets,
        cleaned_datasets=cleaned_datasets,
        features=features,
    )
