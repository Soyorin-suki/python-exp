from flask import Blueprint, request, render_template_string

from ..dao.model_dao import ModelDAO
from ..services.predict_service import get_model_list
from ..services.predict_test_service import get_testable_features, run_prediction_test

bp = Blueprint("predict_test", __name__)

TEST_FORM = """
<h1>随机数据预测测试</h1>
<p>选择一个已训练的模型和数值特征，系统将生成随机测试点并绘制预测曲线与原始数据散点图。</p>

{% if msg %}
<p style="color: {{ color }}">{{ msg }}</p>
{% endif %}

<h2>步骤 1：选择模型与特征</h2>
<form method="post">
    <p>
        <label>模型：</label>
        <select name="model_id">
            {% for m in models %}
            <option value="{{ m.id }}" {% if model_id == m.id %}selected{% endif %}>
                {{ m.model_name }} ({{ m.metadata.model_type }})
            </option>
            {% endfor %}
        </select>
    </p>
    {% if numeric_features %}
    <p>
        <label>测试特征：</label>
        <select name="feature_name">
            {% for feat in numeric_features %}
            <option value="{{ feat }}" {% if feature_name == feat %}selected{% endif %}>{{ feat }}</option>
            {% endfor %}
        </select>
    </p>
    <p>
        <label>测试点数：<input type="number" name="n_points" value="80" min="20" max="500"></label>
    </p>
    {% endif %}
    <p><input type="submit" value="生成预测测试图"></p>
</form>

{% if chart_b64 %}
<h2>预测测试结果</h2>
<p>
    <strong>模型：</strong>{{ model_name }} ({{ model_type }})
    &nbsp;|&nbsp;
    <strong>测试特征：</strong>{{ feature_name }}
</p>
<p style="color: #888;">
    🔵 蓝色散点 = 原始训练数据 &nbsp;|&nbsp;
    🟠 橙色曲线 = 模型预测线（其他特征固定为均值/众数）
</p>
<img src="data:image/png;base64,{{ chart_b64 }}" style="max-width:100%; border:1px solid #ccc;">
{% endif %}

<p><a href="/predict">← 返回房价预测</a> | <a href="/">← 返回首页</a></p>
"""


@bp.route("/predict-test", methods=["GET", "POST"])
def predict_test_view():
    msg = None
    color = "green"
    chart_b64 = None
    model_id = None
    feature_name = None
    model_name = None
    model_type = None
    numeric_features = []
    n_points = 80

    models = get_model_list()

    if request.method == "POST":
        model_id = request.form.get("model_id", type=int)
        feature_name = request.form.get("feature_name", "")
        n_points = request.form.get("n_points", type=int, default=80)

        if not model_id:
            msg = "请选择模型"
            color = "red"
        elif not feature_name:
            msg = "请选择测试特征"
            color = "red"
        else:
            try:
                # Get feature list for the model
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

    # On GET or after POST, show feature list if model selected
    if model_id and not numeric_features:
        try:
            info = get_testable_features(model_id)
            numeric_features = info["numeric_features"]
            model_name = info["model_name"]
            model_type = info["model_type"]
        except Exception:
            pass

    return render_template_string(
        TEST_FORM,
        msg=msg,
        color=color,
        models=models,
        model_id=model_id,
        feature_name=feature_name,
        numeric_features=numeric_features,
        model_name=model_name,
        model_type=model_type,
        chart_b64=chart_b64,
    )
