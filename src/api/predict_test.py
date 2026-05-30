from flask import Blueprint, request, render_template

from ..services.predict_service import get_model_list
from ..services.predict_test_service import (
    get_testable_features,
    run_prediction_test,
    random_spot_check,
)

bp = Blueprint("predict_test", __name__)


@bp.route("/predict-test", methods=["GET", "POST"])
def predict_test_view():
    msg = None
    color = "green"
    chart_b64 = None
    spot_result = None
    model_id = None
    feature_name = None
    model_name = None
    model_type = None
    numeric_features = []
    n_points = 80

    models = get_model_list()

    if request.method == "POST":
        action = request.form.get("action", "plot")
        model_id = request.form.get("model_id", type=int)

        if not model_id:
            msg = "请选择模型"
            color = "red"
        elif action == "spot_check":
            try:
                spot_result = random_spot_check(model_id)
                info = get_testable_features(model_id)
                model_name = info["model_name"]
                model_type = info["model_type"]
                numeric_features = info["numeric_features"]
                msg = "随机抽查完成"
                color = "green"
            except Exception as e:
                msg = f"抽查失败: {e}"
                color = "red"
        else:
            # action == "plot"
            feature_name = request.form.get("feature_name", "")
            n_points = request.form.get("n_points", type=int, default=80)
            if not feature_name:
                msg = "请选择测试特征"
                color = "red"
            else:
                try:
                    info = get_testable_features(model_id)
                    numeric_features = info["numeric_features"]
                    model_name = info["model_name"]
                    model_type = info["model_type"]
                    chart_b64 = run_prediction_test(model_id, feature_name, n_points)
                    msg = "预测测试图已生成"
                    color = "green"
                except Exception as e:
                    msg = f"生成失败: {e}"
                    color = "red"

    # On GET or after error, restore feature list for display
    if model_id and not numeric_features:
        try:
            info = get_testable_features(model_id)
            numeric_features = info["numeric_features"]
            model_name = info["model_name"]
            model_type = info["model_type"]
        except Exception:
            pass

    return render_template(
        "predict_test.html",
        msg=msg,
        color=color,
        models=models,
        model_id=model_id,
        feature_name=feature_name,
        numeric_features=numeric_features,
        model_name=model_name,
        model_type=model_type,
        chart_b64=chart_b64,
        spot_result=spot_result,
    )
