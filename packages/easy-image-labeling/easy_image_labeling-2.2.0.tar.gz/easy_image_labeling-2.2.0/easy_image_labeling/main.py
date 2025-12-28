from easy_image_labeling.cli import stop
from easy_image_labeling.dataset_manager import DatasetManager
from easy_image_labeling import create_app
from flask import Blueprint, g
from flask_wtf import CSRFProtect
from pathlib import Path
from waitress import serve

app = create_app()
csrf = CSRFProtect(app)
csrf._exempt_views.add('dash.dash.dispatch')
bp = Blueprint("main", __name__)

@app.before_request
def get_context() -> None:
    g.dataset_names = sorted(
        map(lambda data: data.address.stem, DatasetManager().managed_datasets)
    )
    g.dataset_num_files = [
        DatasetManager()[dataset_name].num_files for dataset_name in g.dataset_names
    ]

# @app.server.route("/debug-css")
# def debug_css():
#     return {"css": dash_app.css.get_all_css()}


if __name__ == "__main__":
    # serve(app, host="0.0.0.0", port=8080)
    app.run(host="0.0.0.0", port=8000, debug=True)
