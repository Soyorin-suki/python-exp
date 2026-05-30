from flask import Blueprint, request, render_template_string

from ..dao.dataset_dao import DatasetDAO
from ..services.clean_service import clean_dataset, get_dataset_features

bp = Blueprint("clean", __name__)

CLEAN_FORM = """
<h1>数据清洗</h1>
{% if msg %}
<p style="color: {{ color }}">{{ msg }}</p>
{% endif %}

<h2>选择数据集并清洗</h2>
<form method="post">
    <p>
        <label>选择原始数据集：</label>
        <select name="dataset_id">
            {% for ds in raw_datasets %}
            <option value="{{ ds.id }}">{{ ds.filename }}</option>
            {% endfor %}
        </select>
    </p>
    <p>
        <label><input type="checkbox" name="fill_missing" value="1" checked> 缺失值填充（数值→中位数，分类→众数）</label>
    </p>
    <p>
        <label><input type="checkbox" name="remove_outliers" value="1" checked> 异常值处理（IQR方法）</label>
    </p>
    <p>
        <label><input type="checkbox" name="normalize" value="1" checked> 数据标准化（StandardScaler）</label>
    </p>
    <p><input type="submit" value="开始清洗"></p>
</form>

<h2>已清洗的数据集</h2>
<ul>
{% for ds in cleaned_datasets %}
    <li>{{ ds.filename }} — {{ ds.metadata.get('clean_type', '') }} ({{ ds.metadata.get('row_count', '?') }} 行)</li>
{% endfor %}
</ul>

{% if features %}
<h2>数据集特征信息</h2>
<p>目标列: {{ features.target }}</p>
<p>数值特征: {{ features.numeric_features | join(', ') }}</p>
<p>分类特征: {{ features.categorical_features | join(', ') }}</p>
{% endif %}

<p><a href="/">← 返回首页</a></p>
"""


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

    return render_template_string(
        CLEAN_FORM,
        msg=msg,
        color=color,
        raw_datasets=raw_datasets,
        cleaned_datasets=cleaned_datasets,
        features=features,
    )
