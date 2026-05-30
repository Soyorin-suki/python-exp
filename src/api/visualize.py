from flask import Blueprint, request, render_template

from ..dao.dataset_dao import DatasetDAO
from ..services.visualize_service import (
    generate_histogram,
    generate_scatter,
    generate_correlation_heatmap,
    get_available_charts,
)

bp = Blueprint("visualize", __name__)

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

    return render_template(
        "visualize.html",
        msg=msg,
        color=color,
        datasets=datasets,
        numeric_cols=numeric_cols,
        chart_b64=chart_b64,
    )
