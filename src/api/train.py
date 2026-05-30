from flask import Blueprint, request, render_template_string

from ..dao.dataset_dao import DatasetDAO
from ..dao.model_dao import ModelDAO
from ..services.train_service import train_sklearn, train_pytorch

bp = Blueprint("train", __name__)

TRAIN_FORM = """
<h1>模型训练</h1>
{% if msg %}
<p style="color: {{ color }}">{{ msg }}</p>
{% endif %}

<h2>选择数据集与算法</h2>
<form method="post">
    <p>
        <label>选择已清洗的数据集：</label>
        <select name="dataset_id">
            {% for ds in cleaned_datasets %}
            <option value="{{ ds.id }}">{{ ds.filename }}</option>
            {% endfor %}
        </select>
    </p>
    <p>
        <label>算法类型：</label>
        <select name="model_type">
            <option value="sklearn">sklearn — LinearRegression</option>
            <option value="pytorch">pytorch — 全连接神经网络</option>
        </select>
    </p>
    <p>
        <label>测试集比例：<input type="number" name="test_size" value="0.2" step="0.05" min="0.1" max="0.4"></label>
    </p>
    <p><input type="submit" value="开始训练"></p>
</form>

{% if result %}
<h2>训练结果</h2>
<table border="1" cellpadding="6">
    <tr><td>模型名称</td><td>{{ result.model_name }}</td></tr>
    <tr><td>MSE</td><td>{{ "%.4f" | format(result.mse) }}</td></tr>
    <tr><td>RMSE</td><td>{{ "%.4f" | format(result.rmse) }}</td></tr>
    <tr><td>R²</td><td>{{ "%.4f" | format(result.r2) }}</td></tr>
    <tr><td>训练集行数</td><td>{{ result.train_rows }}</td></tr>
    <tr><td>测试集行数</td><td>{{ result.test_rows }}</td></tr>
    <tr><td>数值特征</td><td>{{ result.numeric_features | join(', ') }}</td></tr>
    <tr><td>分类特征</td><td>{{ result.categorical_features | join(', ') }}</td></tr>
</table>
{% endif %}

<h2>已训练的模型</h2>
<ul>
{% for m in models %}
    <li>
        {{ m.model_name }}
        — 类型: {{ m.metadata.model_type }}
        — MSE: {{ "%.2f" | format(m.metadata.mse) if m.metadata.mse else 'N/A' }}
        — R²: {{ "%.4f" | format(m.metadata.r2) if m.metadata.r2 else 'N/A' }}
    </li>
{% endfor %}
</ul>

<p><a href="/">← 返回首页</a></p>
"""


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

    return render_template_string(
        TRAIN_FORM,
        msg=msg,
        color=color,
        cleaned_datasets=cleaned_datasets,
        models=models,
        result=result,
    )
