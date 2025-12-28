import pandas as pd
from pathlib import Path
from io import StringIO
from dash import Dash, Input, Output
from dash.exceptions import PreventUpdate
from easy_image_labeling.plotlydash.data.source import DataSchema, DataSource
from easy_image_labeling.plotlydash.components import ids
from easy_image_labeling.db.db import sqlite_connection


def init_load_data_callback(dash_app: Dash, db_path: Path):
    @dash_app.callback(
        Output(ids.DATA_STORE, "data"), Input(ids.REGENERATE_BUTTON, "n_clicks")
    )
    def load_image_metadata(n) -> str:
        """Load image metadata SQLite database with pandas."""

        if not n:
            raise PreventUpdate

        with sqlite_connection(db_path) as cur:
            data = pd.read_sql(
                """
                SELECT *
                FROM Image
                """,
                cur.connection,
                dtype={
                    DataSchema.ImageId: int,
                    DataSchema.Dataset: str,
                    DataSchema.ImageName: str,
                    DataSchema.DatasetID: int,
                    DataSchema.LabelName: str,
                    DataSchema.LastLabelDate: str,
                },
                parse_dates={DataSchema.LastLabelDate: r"%Y-%m-%d %H:%M:%S.%f"},
            ).to_json(date_format="iso")

        return data


def load_data_from_store(json: str) -> DataSource:
    df = pd.read_json(StringIO(json))
    df[DataSchema.LastLabelDate] = pd.to_datetime(df[DataSchema.LastLabelDate])
    return DataSource(df)
