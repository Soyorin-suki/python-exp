import json

from flask import Blueprint, request, render_template

from ..dao.model_dao import ModelDAO
from ..services.predict_service import get_model_list, get_model_detail, predict
from ..services.predict_test_service import random_spot_check

bp = Blueprint("analysis", __name__)


def _load_feature_info(model: dict) -> tuple[list, list, dict]:
    """Extract (numeric_features, categorical_features, category_options) from a model record."""
    path = model["metadata"].get("feature_info_path")
    if path:
        with open(path, "r", encoding="utf-8") as f:
            fi = json.load(f)
            return (
                fi.get("numeric_features", []),
                fi.get("categorical_features", []),
                fi.get("category_values", {}),
            )
    return (
        model["metadata"].get("numeric_features", []),
        model["metadata"].get("categorical_features", []),
        {},
    )


@bp.route("/predict", methods=["GET", "POST"])
def predict_view():
    msg = None
    color = "green"
    selected_model = None
    numeric_features = []
    categorical_features = []
    category_options = {}
    prediction = None
    spot_result = None

    models = get_model_list()
    step = request.args.get("step", "select")

    if request.method == "POST":
        model_id = request.form.get("model_id", type=int)
        action = request.form.get("action", "")

        # --- Random spot check ---
        if action == "spot_check" and model_id:
            try:
                selected_model = get_model_detail(model_id)
                numeric_features, categorical_features, category_options = _load_feature_info(selected_model)
                spot_result = random_spot_check(model_id)
                msg = "随机抽查完成"
                color = "green"
            except Exception as e:
                msg = f"抽查失败: {e}"
                color = "red"

        else:
            has_feature_input = any(k.startswith("feat_") for k in request.form)

            if step == "select" or (step == "predict" and not has_feature_input):
                if model_id:
                    try:
                        selected_model = get_model_detail(model_id)
                        numeric_features, categorical_features, category_options = _load_feature_info(selected_model)
                    except Exception as e:
                        msg = f"加载模型详情失败: {e}"
                        color = "red"

            elif step == "predict":
                if model_id:
                    try:
                        selected_model = get_model_detail(model_id)
                        numeric_features, categorical_features, category_options = _load_feature_info(selected_model)

                        feature_values = {}
                        for feat in numeric_features + categorical_features:
                            val = request.form.get(f"feat_{feat}")
                            if val is not None and val != "":
                                feature_values[feat] = val

                        prediction = predict(model_id, feature_values)
                        msg = "预测完成"
                        color = "green"
                    except Exception as e:
                        msg = f"预测失败: {e}"
                        color = "red"

    return render_template(
        "analysis.html",
        msg=msg,
        color=color,
        models=models,
        selected_model=selected_model,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        category_options=category_options,
        prediction=prediction,
        spot_result=spot_result,
    )
