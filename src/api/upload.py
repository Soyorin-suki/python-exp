from flask import Blueprint, request, render_template_string

from ..services.dataset_service import save_dataset
from ..dao.dataset_dao import DatasetDAO

bp = Blueprint("upload", __name__)

UPLOAD_FORM = """
<h1>上传数据集</h1>
{% if msg %}
<p style="color: {{ color }}">{{ msg }}</p>
{% endif %}
<form method="post" enctype="multipart/form-data">
    <p><input type="file" name="file" accept=".csv,.xlsx"></p>
    <p>支持 CSV 和 XLSX 格式，不允许重名文件</p>
    <p><input type="submit" value="上传"></p>
</form>
<p><a href="/">← 返回首页</a></p>
<h2>已有数据集</h2>
<ul>
{% for ds in datasets %}
    <li>{{ ds.filename }}</li>
{% endfor %}
</ul>
"""


@bp.route("/upload", methods=["GET", "POST"])
def upload_dataset():
    msg = None
    color = "green"

    if request.method == "POST":
        if "file" not in request.files:
            msg = "未选择文件"
            color = "red"
        else:
            file = request.files["file"]
            try:
                filename = save_dataset(file)
                msg = f"文件 {filename} 上传成功"
                color = "green"
            except FileExistsError as e:
                msg = str(e)
                color = "red"
            except ValueError as e:
                msg = str(e)
                color = "red"
            except Exception as e:
                msg = f"上传失败: {e}"
                color = "red"

    dao = DatasetDAO()
    datasets = dao.get_all()
    return render_template_string(UPLOAD_FORM, msg=msg, color=color, datasets=datasets)
