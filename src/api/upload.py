from flask import Blueprint, request, render_template

from ..dao.dataset_dao import DatasetDAO
from ..services.dataset_service import save_dataset

bp = Blueprint("upload", __name__)


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
    return render_template("upload.html", msg=msg, color=color, datasets=datasets)
