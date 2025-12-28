from dash import Dash, dcc, html, Input, Output
import plotly.express as px
from easy_image_labeling.plotlydash.data.data_loader import load_data_from_store
from easy_image_labeling.plotlydash.data.source import DataSchema
from easy_image_labeling.plotlydash.components import ids


def render(app: Dash) -> html.Div:
    @app.callback(
        Output(ids.PIE_CHART, "children"),
        [Input(ids.DATASET_DROPDOWN, "value"), Input(ids.DATA_STORE, "data")],
    )
    def update_pie_chart(dataset: str, json_data: str) -> html.Div:
        filtered_source = load_data_from_store(json_data).filter_by_datasets([dataset])
        if not filtered_source.row_count:
            return html.Div("No data", id=ids.PIE_CHART)
        class_sizes = filtered_source.get_size_of_groups(DataSchema.LabelName)
        fig = px.pie(
            class_sizes,
            values="count",
            names=DataSchema.LabelName,
            hole=0.5,
        )
        return html.Div(
            html.Div(
                [
                    html.H3("Class size distribution"),
                    dcc.Graph(figure=fig),
                ],
            ),
            className="pie_chart",
            id=ids.PIE_CHART,
        )

    return html.Div(id=ids.PIE_CHART)
