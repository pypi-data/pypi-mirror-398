from pathlib import Path
from easy_image_labeling.exceptions import MissingSecretEnvFile

type AppConfig = type[DevConfig] | type[ProdConfig] | type[TestConfig]


class Config:
    try:
        with open(Path(__file__).parent.parent / "secret.env") as f:
            SECRET_KEY = f.read()
    except FileNotFoundError:
        raise MissingSecretEnvFile(
            "No 'secret.env' file found. This file is used to store"
            " your flask CSRF secret key. If this is your fist time"
            " using easy_image_labeling you need to create this file"
            f" at {(Path(__file__).parent.parent / "secret.env")}"
            " and insert your secret key. To learn more about CSRF"
            " protection in flask you can visit"
            " https://flask-wtf.readthedocs.io/en/0.15.x/csrf/."
        )
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 10MB
    DATASET_FOLDER = Path(__file__).parent / "static" / "datasets"
    DB_URL = Path(__file__).parent / "db" / "database.sqlite"
    DB_SCHEMA = Path(__file__).parent / "db" / "schema.sql"
    UPLOAD_FOLDER = Path(__file__).parent / "uploads"
    UPLOAD_FILENAME = "LabelingResults"


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False


class TestConfig:
    with open(Path(__file__).parent.parent / "secret.env") as f:
        SECRET_KEY = f.read()
    DEBUG = False
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 10MB
    DATASET_FOLDER = Path(__file__).parent.parent / "tests" / "datasets"
    DB_URL = Path(__file__).parent.parent / "tests" / "test_db.sqlite"
    DB_SCHEMA = Path(__file__).parent / "db" / "schema.sql"
    UPLOAD_FOLDER = Path(__file__).parent.parent / "tests" / "uploads"
    UPLOAD_FILENAME = "LabelingResults"
    WTF_CSRF_ENABLED = False
