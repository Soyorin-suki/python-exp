import json

from flask import Blueprint, request, render_template

from ..dao.model_dao import ModelDAO
from ..services.predict_service import get_model_list, get_model_detail, predict

bp = Blueprint("analysis", __name__)


@bp.route("/predict", methods=["GET", "POST"])
def predict_view():
    msg = None
    color = "green"
    selected_model = None
    numeric_features = []
    categorical_features = []
    category_options = {}
    prediction = None

    mdl_dao = ModelDAO()
    models = get_model_list()

    step = request.args.get("step", "select")

    if request.method == "POST":
        model_id = request.form.get("model_id", type=int)

        # Detect whether user submitted feature values (fields like "feat_xxx")
        has_feature_input = any(k.startswith("feat_") for k in request.form)

        if step == "select" or (step == "predict" and not has_feature_input):
            # User selected a model — show details + feature form
            if model_id:
                try:
                    selected_model = get_model_detail(model_id)
                    feature_info_path = selected_model["metadata"].get("feature_info_path")
                    if feature_info_path:
                        with open(feature_info_path, "r", encoding="utf-8") as f:
                            fi = json.load(f)
                            numeric_features = fi.get("numeric_features", [])
                            categorical_features = fi.get("categorical_features", [])
                            category_options = fi.get("category_values", {})
                    else:
                        numeric_features = selected_model["metadata"].get("numeric_features", [])
                        categorical_features = selected_model["metadata"].get("categorical_features", [])
                except Exception as e:
                    msg = f"加载模型详情失败: {e}"
                    color = "red"

        elif step == "predict":
            # User submitted feature values — run prediction
            if model_id:
                try:
                    selected_model = get_model_detail(model_id)
                    feature_info_path = selected_model["metadata"].get("feature_info_path")
                    if feature_info_path:
                        with open(feature_info_path, "r", encoding="utf-8") as f:
                            fi = json.load(f)
                            numeric_features = fi.get("numeric_features", [])
                            categorical_features = fi.get("categorical_features", [])
                            category_options = fi.get("category_values", {})

                    # Collect feature values from form
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
    )
