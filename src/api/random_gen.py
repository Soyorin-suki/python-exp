from flask import Blueprint, request, render_template

bp = Blueprint("random_gen", __name__)


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

    return render_template("random_gen.html", msg=msg, color=color)
