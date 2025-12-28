import csv
import json
from werkzeug.security import safe_join
from easy_image_labeling.db.db import LabeledImage, LabeledImageColumns
from flask import current_app


def _safe_join(folder: str, filename: str) -> str:
    filepath = safe_join(folder, filename)
    if filepath is None:
        raise ValueError("Error while trying to join UPLOAD_FOLDER and UPLOAD_FILENAME")
    return filepath


def write_to_csv(results: list[LabeledImage]) -> None:
    """Write results to csv file."""

    filepath = _safe_join(
        str(current_app.config["UPLOAD_FOLDER"]),
        str(current_app.config["UPLOAD_FILENAME"]),
    )

    with open(filepath, "w") as result_file:
        csv_writer = csv.writer(result_file)
        csv_writer.writerow(LabeledImageColumns)
        csv_writer.writerows(results)


def write_to_json(results: list[LabeledImage]) -> None:
    """Write results to json file."""

    filepath = _safe_join(
        str(current_app.config["UPLOAD_FOLDER"]),
        str(current_app.config["UPLOAD_FILENAME"]),
    )

    results_dict = {image_name: label_name for _, image_name, label_name in results}
    with open(filepath, "w") as result_file:
        json.dump(results_dict, result_file)
