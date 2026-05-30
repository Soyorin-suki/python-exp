from flask import Blueprint, request, render_template_string

from ..dao import RAW_DIR, ensure_data_dirs
from ..dao.dataset_dao import DatasetDAO
from ..services.dataset_service import save_dataset as _svc_save

bp = Blueprint("random_gen", __name__)

GEN_FORM = """
<h1>生成测试数据</h1>
{% if msg %}
<p style="color: {{ color }}">{{ msg }}</p>
{% endif %}

<h2>选择生成模式</h2>
<form method="post">
    <p>
        <label><input type="radio" name="gen_type" value="linear" checked> 线性回归数据（y = a·x + b + noise）</label>
    </p>
    <p>
        <label><input type="radio" name="gen_type" value="polynomial"> 多项式数据（y = a·x² + b·x + c + noise）</label>
    </p>
    <p>
        <label>样本数量：<input type="number" name="n_samples" value="500" min="100" max="10000"></label>
    </p>
    <p>
        <label>噪声水平：<input type="number" name="noise" value="0.1" step="0.05" min="0" max="1"></label>
    </p>
    <p>
        <label>文件名：<input type="text" name="filename" value="synthetic_data.csv" required></label>
    </p>
    <p><input type="submit" value="生成并保存"></p>
</form>

<p><a href="/">← 返回首页</a></p>
"""


@bp.route("/random-gen", methods=["GET", "POST"])
def random_gen_view():
    msg = None
    color = "green"

    if request.method == "POST":
        gen_type = request.form.get("gen_type", "linear")
        n_samples = request.form.get("n_samples", type=int, default=500)
        noise = request.form.get("noise", type=float, default=0.1)
        filename = request.form.get("filename", "synthetic_data.csv")

        if not filename.endswith(".csv"):
            filename += ".csv"

        try:
            from ..services.random_gen_service import generate_and_save
            result = generate_and_save(gen_type, n_samples, noise, filename)
            msg = f"测试数据集已生成: {result}"
            color = "green"
        except FileExistsError as e:
            msg = str(e)
            color = "red"
        except Exception as e:
            msg = f"生成失败: {e}"
            color = "red"

    return render_template_string(GEN_FORM, msg=msg, color=color)
