from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from easy_image_labeling.plotlydash.components import (
    ids,
    sidebar,
    pie_chart,
    progress_chart,
)


def render(app: Dash):
    _button = dbc.Button(
        "Reload data",
        color="primary",
        id=ids.REGENERATE_BUTTON,
        n_clicks=1,
        className="regenerate_button",
    )
    _data_store = dcc.Store(id=ids.DATA_STORE, storage_type="session")
    _side_bar = sidebar.render(app)
    _pie_chart = pie_chart.render(app)
    _progress_chart = progress_chart.render(app)
    content = html.Div(
        [
            _button,
            _data_store,
            _pie_chart,
            _progress_chart,
        ],
        id=ids.LAYOUT,
        className="content",
    )
    return html.Div([_side_bar, content], className="page")
