import os
from typing import Literal
from easy_image_labeling.exceptions import MissingSecretEnvFile
from easy_image_labeling.helper_functions import create_env_file_with_provided_key

try:
    from easy_image_labeling.config import ProdConfig, DevConfig, TestConfig
except MissingSecretEnvFile as e:
    print(e)
    if input("Would you like to automatically create this file? (Y/n)\n") == "Y":
        create_env_file_with_provided_key()
        from easy_image_labeling.config import ProdConfig, DevConfig, TestConfig
    else:
        raise RuntimeError
from easy_image_labeling.db.db import sqlite_connection
from easy_image_labeling.pages import selection
from easy_image_labeling.pages import classify
from easy_image_labeling.pages import export
from flask import Flask, current_app, render_template
from .plotlydash.dashboard import initiatlize_dashboard
from easy_image_labeling.dataset_manager import Dataset, DatasetManager
from pathlib import Path

__version__ = "2.2.0"


def create_app(
    mode: Literal["production", "develope", "testing"] = "production",
) -> Flask:
    app = Flask(__name__, template_folder="./templates")
    config = dict(production=ProdConfig, develope=DevConfig, testing=TestConfig)[mode]
    app.config.from_object(config)
    app.register_blueprint(selection.bp)
    app.register_blueprint(classify.bp)
    app.register_blueprint(export.bp)
    app.jinja_env.filters["zip"] = zip
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    fetch_existing_datasets(app)
    initialize_database(app)
    with app.app_context():
        dash_app = initiatlize_dashboard(app, config)
    setattr(app, "dash_app", dash_app)

    @app.route("/", methods=["POST", "GET"])
    @app.route("/index", methods=["POST", "GET"])
    def index():
        # print(list(map(lambda data: data.address.stem, DatasetManager().managed_datasets)))
        # dataset_name = session["datasets"][0]
        # DatasetManager().remove(dataset_name)
        return render_template("index.html")

    return app


def fetch_existing_datasets(app: Flask) -> None:
    with app.app_context():
        dataset_folder = current_app.config.get("DATASET_FOLDER", None)
        Dataset.dataset_root_folder = current_app.config["DATASET_FOLDER"]
    if dataset_folder is None:
        raise RuntimeError("DATASET_FOLDER missing in app config.")
    for dataset_path in Path(dataset_folder).glob("*"):
        DatasetManager().add(Dataset(dataset_path))


def initialize_database(app: Flask) -> None:
    with app.app_context():
        db_path = current_app.config.get("DB_URL", None)
        db_schema_path: Path | None = current_app.config.get("DB_SCHEMA", None)
        for parameter in ("DB_URL", "DB_SCHEMA"):
            if current_app.config.get(parameter, None) is None:
                raise RuntimeError(f"{parameter} missing in app config.")
        if db_schema_path is None:
            raise KeyError("DB_SCHEMA parameter is missing in app config.")
        if not db_schema_path.exists():
            raise RuntimeError(f"Database schema file {db_schema_path} does not exist.")
        with sqlite_connection(db_path) as cur:
            cur.executescript(db_schema_path.read_text(encoding="utf8"))
