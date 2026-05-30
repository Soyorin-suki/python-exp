from flask import Blueprint, request, render_template

from ..dao.dataset_dao import DatasetDAO
from ..dao.model_dao import ModelDAO
from ..services.train_service import train_sklearn, train_pytorch

bp = Blueprint("train", __name__)


@bp.route("/train", methods=["GET", "POST"])
def train_view():
    msg = None
    color = "green"
    result = None

    ds_dao = DatasetDAO()
    mdl_dao = ModelDAO()
    cleaned_datasets = ds_dao.get_cleaned_datasets()
    models = mdl_dao.get_all()

    if request.method == "POST":
        dataset_id = request.form.get("dataset_id", type=int)
        model_type = request.form.get("model_type", "sklearn")
        test_size = request.form.get("test_size", type=float, default=0.2)

        if not dataset_id:
            msg = "请选择数据集"
            color = "red"
        else:
            try:
                if model_type == "sklearn":
                    result = train_sklearn(dataset_id, test_size=test_size)
                elif model_type == "pytorch":
                    result = train_pytorch(dataset_id, test_size=test_size)
                else:
                    msg = f"不支持的模型类型: {model_type}"
                    color = "red"
                if result:
                    msg = f"模型训练完成: {result['model_name']}"
                    color = "green"
                    models = mdl_dao.get_all()
            except ImportError as e:
                msg = str(e)
                color = "red"
            except Exception as e:
                msg = f"训练失败: {e}"
                color = "red"

    return render_template(
        "train.html",
        msg=msg,
        color=color,
        cleaned_datasets=cleaned_datasets,
        models=models,
        result=result,
    )
