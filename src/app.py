from flask import Flask, render_template

from .api.upload import bp as upload_bp
from .api.clean import bp as clean_bp
from .api.train import bp as train_bp
from .api.analysis import bp as analysis_bp
from .api.visualize import bp as visualize_bp
from .api.random_gen import bp as random_gen_bp

app = Flask(__name__)
app.register_blueprint(upload_bp)
app.register_blueprint(clean_bp)
app.register_blueprint(train_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(visualize_bp)
app.register_blueprint(random_gen_bp)


@app.route("/")
def hello_world():
    return render_template("index.html")


def main():
    app.run()


if __name__ == "__main__":
    main()
