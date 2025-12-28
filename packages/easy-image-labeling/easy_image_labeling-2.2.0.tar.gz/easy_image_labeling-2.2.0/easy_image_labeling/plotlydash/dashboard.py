from dash import Dash
from pathlib import Path
import dash_bootstrap_components as dbc
from easy_image_labeling.config import AppConfig
from easy_image_labeling.plotlydash.data.data_loader import init_load_data_callback
from easy_image_labeling.plotlydash.components import layout

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100..900;1,100..900&display=swap"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
    dbc.themes.BOOTSTRAP,
]


def initiatlize_dashboard(server, config: AppConfig):
    """Create a Plotly Dash dashboard."""
    assets_path = Path(__file__).parent / "assets"

    dash_app = Dash(
        __name__,
        server=server,
        routes_pathname_prefix="/analytics/",
        external_stylesheets=["/static/style.css", *external_stylesheets],
        title="Easy image labeling - Analytics",
        assets_folder=str(assets_path),
    )
    init_load_data_callback(dash_app, config.DB_URL)
    dash_app.layout = layout.render(dash_app)
    return dash_app
