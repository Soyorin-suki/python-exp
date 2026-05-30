from flask import Blueprint, request, render_template_string

from ..dao.dataset_dao import DatasetDAO
from ..services.visualize_service import (
    generate_histogram,
    generate_scatter,
    generate_correlation_heatmap,
    get_available_charts,
)

bp = Blueprint("visualize", __name__)

VIS_FORM = """
<h1>数据可视化</h1>
{% if msg %}
<p style="color: {{ color }}">{{ msg }}</p>
{% endif %}

<h2>选择数据集和图表类型</h2>
<form method="post">
    <p>
        <label>数据集：</label>
        <select name="dataset_id">
            {% for ds in datasets %}
            <option value="{{ ds.id }}">{{ ds.filename }}</option>
            {% endfor %}
        </select>
    </p>
    <p>
        <label>图表类型：</label>
        <select name="chart_type" id="chart_type" onchange="toggleColumns()">
            <option value="histogram">直方图</option>
            <option value="scatter">散点图</option>
            <option value="correlation">相关性热力图</option>
        </select>
    </p>
    <div id="single_col_div">
        <p>
            <label>数值列：</label>
            <select name="column">
                {% for col in numeric_cols %}
                <option value="{{ col }}">{{ col }}</option>
                {% endfor %}
            </select>
        </p>
    </div>
    <div id="two_col_div" style="display:none">
        <p>
            <label>X 轴列：</label>
            <select name="x_col">
                {% for col in numeric_cols %}
                <option value="{{ col }}">{{ col }}</option>
                {% endfor %}
            </select>
        </p>
        <p>
            <label>Y 轴列：</label>
            <select name="y_col">
                {% for col in numeric_cols %}
                <option value="{{ col }}">{{ col }}</option>
                {% endfor %}
            </select>
        </p>
    </div>
    <p><input type="submit" value="生成图表"></p>
</form>

{% if chart_b64 %}
<h2>图表结果</h2>
<img src="data:image/png;base64,{{ chart_b64 }}" style="max-width:100%; border:1px solid #ccc;">
{% endif %}

<script>
function toggleColumns() {
    var type = document.getElementById('chart_type').value;
    document.getElementById('single_col_div').style.display = (type === 'histogram') ? 'block' : 'none';
    document.getElementById('two_col_div').style.display = (type === 'scatter') ? 'block' : 'none';
}
</script>

<p><a href="/">← 返回首页</a></p>
"""


@bp.route("/visualize", methods=["GET", "POST"])
def visualize_view():
    msg = None
    color = "green"
    chart_b64 = None

    dao = DatasetDAO()
    datasets = dao.get_all()

    # Get numeric columns from first dataset for form defaults
    numeric_cols = []
    if datasets:
        try:
            chart_info = get_available_charts(datasets[0]["id"])
            numeric_cols = chart_info["numeric_columns"]
        except Exception:
            pass

    if request.method == "POST":
        dataset_id = request.form.get("dataset_id", type=int)
        chart_type = request.form.get("chart_type", "histogram")

        if not dataset_id:
            msg = "请选择数据集"
            color = "red"
        else:
            try:
                # Get numeric columns for this dataset
                chart_info = get_available_charts(dataset_id)
                numeric_cols = chart_info["numeric_columns"]

                if chart_type == "histogram":
                    column = request.form.get("column", numeric_cols[0] if numeric_cols else "")
                    if not column:
                        msg = "请选择数值列"
                        color = "red"
                    else:
                        chart_b64 = generate_histogram(dataset_id, column)

                elif chart_type == "scatter":
                    x_col = request.form.get("x_col")
                    y_col = request.form.get("y_col")
                    if len(numeric_cols) >= 2:
                        x_col = x_col or numeric_cols[0]
                        y_col = y_col or numeric_cols[1]
                    if not x_col or not y_col:
                        msg = "请选择 X 轴和 Y 轴列"
                        color = "red"
                    else:
                        chart_b64 = generate_scatter(dataset_id, x_col, y_col)

                elif chart_type == "correlation":
                    chart_b64 = generate_correlation_heatmap(dataset_id)

                if chart_b64:
                    msg = "图表生成成功"
                    color = "green"
            except Exception as e:
                msg = f"生成失败: {e}"
                color = "red"

    return render_template_string(
        VIS_FORM,
        msg=msg,
        color=color,
        datasets=datasets,
        numeric_cols=numeric_cols,
        chart_b64=chart_b64,
    )
