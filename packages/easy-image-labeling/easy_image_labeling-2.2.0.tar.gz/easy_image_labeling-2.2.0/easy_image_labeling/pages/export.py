from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    current_app,
    request,
    g,
    flash,
    send_from_directory,
)
from pathlib import Path
from easy_image_labeling.forms import ExportLabelsForm
from easy_image_labeling.db.db import sqlite_connection, get_results_by_dataset
from easy_image_labeling.result_writers import write_to_csv, write_to_json

EXPORT_METHODS = ["JSON", "csv"]

bp = Blueprint("export", __name__)


def create_export_labels_form():
    form = ExportLabelsForm()
    form.dataset_selection_field.choices.extend([(dataset, dataset) for dataset in g.dataset_names])  # type: ignore
    form.export_selection_field.choices.extend([(export_method, export_method) for export_method in EXPORT_METHODS])  # type: ignore
    return form


@bp.route("/export", methods=["POST", "GET"])
def export_results():
    export_labels_form = create_export_labels_form()
    return render_template("export_results.html", form=export_labels_form)


@bp.route("/export/submit_export", methods=["POST", "GET"])
def submit_export_results():
    if request.method == "POST":
        export_labels_form = ExportLabelsForm()
        export_labels_form.process(request.form)
        dataset_to_export = export_labels_form.data["dataset_selection_field"]
        export_format = export_labels_form.data["export_selection_field"]
        if not Path(current_app.config["UPLOAD_FOLDER"]).is_dir():
            Path(current_app.config["UPLOAD_FOLDER"]).mkdir()
    return redirect(
        url_for(
            "export.download_file",
            dataset=dataset_to_export,
            export_format=export_format,
        )
    )


@bp.route("/export/uploads/<dataset>/<export_format>", methods=["POST", "GET"])
def download_file(dataset: str, export_format: str):
    with sqlite_connection(current_app.config["DB_URL"]) as cur:
        results = get_results_by_dataset(cur, dataset)

    result_writers = {"csv": write_to_csv, "json": write_to_json}
    try:
        result_writers[export_format.lower()](results)
    except Exception as e:
        flash(f"Error while trying to fetch results:\n{e}")
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        current_app.config["UPLOAD_FILENAME"],
        as_attachment=True,
        download_name=str(
            Path(f"{current_app.config["UPLOAD_FILENAME"]}_{dataset}").with_suffix(
                f".{export_format.lower()}"
            )
        ),
    )
