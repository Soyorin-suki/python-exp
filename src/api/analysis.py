import json

from flask import Blueprint, request, render_template_string

from ..dao.model_dao import ModelDAO
from ..services.predict_service import get_model_list, get_model_detail, predict

bp = Blueprint("analysis", __name__)

PREDICT_FORM = """
<h1>房价预测</h1>
{% if msg %}
<p style="color: {{ color }}">{{ msg }}</p>
{% endif %}

<h2>步骤 1：选择模型</h2>
<form method="post" action="?step=select">
    <select name="model_id">
        {% for m in models %}
        <option value="{{ m.id }}" {% if selected_model and selected_model.id == m.id %}selected{% endif %}>
            {{ m.model_name }} ({{ m.metadata.model_type }})
        </option>
        {% endfor %}
    </select>
    <input type="submit" value="查看模型详情">
</form>

{% if selected_model %}
<h2>步骤 2：模型详情</h2>
<table border="1" cellpadding="6">
    <tr><td>模型名称</td><td>{{ selected_model.model_name }}</td></tr>
    <tr><td>模型类型</td><td>{{ selected_model.metadata.model_type }}</td></tr>
    <tr><td>MSE</td><td>{{ "%.4f" | format(selected_model.metadata.mse) if selected_model.metadata.mse else 'N/A' }}</td></tr>
    <tr><td>RMSE</td><td>{{ "%.4f" | format(selected_model.metadata.rmse) if selected_model.metadata.rmse else 'N/A' }}</td></tr>
    <tr><td>R²</td><td>{{ "%.4f" | format(selected_model.metadata.r2) if selected_model.metadata.r2 else 'N/A' }}</td></tr>
    <tr><td>训练集行数</td><td>{{ selected_model.metadata.train_rows }}</td></tr>
    <tr><td>测试集行数</td><td>{{ selected_model.metadata.test_rows }}</td></tr>
</table>

<h2>步骤 3：输入特征值进行预测</h2>
<form method="post" action="?step=predict">
    <input type="hidden" name="model_id" value="{{ selected_model.id }}">
    {% if numeric_features %}
    <h3>数值特征</h3>
    {% for feat in numeric_features %}
    <p><label>{{ feat }}：<input type="number" name="feat_{{ feat }}" step="any" required></label></p>
    {% endfor %}
    {% endif %}
    {% if categorical_features %}
    <h3>分类特征</h3>
    {% for feat in categorical_features %}
    <p><label>{{ feat }}：<input type="text" name="feat_{{ feat }}" required></label></p>
    {% endfor %}
    {% endif %}
    <p><input type="submit" value="预测"></p>
</form>
{% endif %}

{% if prediction is not none %}
<h2>预测结果</h2>
<p style="font-size: 1.5em; color: #2a7d2a;">预测房价: ₹ {{ "%.2f" | format(prediction) }}</p>
{% endif %}

<p><a href="/">← 返回首页</a></p>
"""


@bp.route("/predict", methods=["GET", "POST"])
def predict_view():
    msg = None
    color = "green"
    selected_model = None
    numeric_features = []
    categorical_features = []
    prediction = None

    mdl_dao = ModelDAO()
    models = get_model_list()

    step = request.args.get("step", "select")

    if request.method == "POST":
        model_id = request.form.get("model_id", type=int)

        if step == "select" or (step == "predict" and not request.form.get("feat_")):
            # User selected a model — show details + feature form
            if model_id:
                try:
                    selected_model = get_model_detail(model_id)
                    # Load feature info
                    feature_info_path = selected_model["metadata"].get("feature_info_path")
                    if feature_info_path:
                        with open(feature_info_path, "r", encoding="utf-8") as f:
                            fi = json.load(f)
                            numeric_features = fi.get("numeric_features", [])
                            categorical_features = fi.get("categorical_features", [])
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

    return render_template_string(
        PREDICT_FORM,
        msg=msg,
        color=color,
        models=models,
        selected_model=selected_model,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        prediction=prediction,
    )
