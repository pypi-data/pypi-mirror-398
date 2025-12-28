from dash import Dash, dcc, html, Input, Output
import calendar
import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objects import Figure
from datetime import timedelta, datetime
from easy_image_labeling.plotlydash.data.data_loader import load_data_from_store
from easy_image_labeling.plotlydash.data.source import DataSchema
from easy_image_labeling.plotlydash.components import ids
from easy_image_labeling.helper_functions import (
    TimeIntervals,
    _get_number_of_days_in_month,
)

hovertemplates = {
    "day": "%{x|%e %b, %Y}<br>Labeled images: %{customdata[0]}",
    "week": "Week of %{x|%e %b, %Y}<br>Labeled images: %{customdata[0]}",
    "month": "Month of %{x|%b, %Y}<br>Labeled images: %{customdata[0]}",
}

milliseconds_per_day = 1000 * 3600 * 24


def render(app: Dash) -> html.Div:
    @app.callback(
        Output(ids.PROGRESS_CHART, "children"),
        [
            Input(ids.DATASET_DROPDOWN, "value"),
            Input(ids.DATA_STORE, "data"),
            Input(ids.TIME_INTERVAL_DROPDOWN, "value"),
        ],
    )
    def update_progress_chart(
        dataset: str, json_data: str, time_interval: TimeIntervals
    ) -> html.Div:
        filtered_source = load_data_from_store(json_data).filter_by_datasets([dataset])
        if not filtered_source.row_count:
            return html.Div("No data", id=ids.PROGRESS_CHART)
        progress_data = filtered_source.get_progress_per_time_interval(time_interval)
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=progress_data[DataSchema.LastLabelDate],
                y=progress_data["count"],
                xperiod=milliseconds_per_day if not time_interval == "month" else "M1",
                xperiodalignment="middle",
            )
        )
        _configure_plotly_figure(fig, progress_data, time_interval)
        return html.Div(
            html.Div(
                [
                    html.H3("Labeled images over the last 6 months"),
                    dcc.Graph(figure=fig),
                ],
            ),
            className="progress_chart",
            id=ids.PROGRESS_CHART,
        )

    return html.Div(id=ids.PROGRESS_CHART)


def _configure_plotly_figure(
    fig: Figure, progress_data: pd.DataFrame, time_interval: TimeIntervals
):
    fig.update_yaxes(dtick=1, ticklabelmode="period")
    first_displayed_date = datetime.today() - timedelta(days=182)
    if time_interval == "day":
        fig.update_xaxes(
            range=[first_displayed_date, datetime.today()],
        )
        fig.update_traces(
            width=milliseconds_per_day,
            customdata=progress_data[["count"]],
            hovertemplate=hovertemplates["day"],
        )
    elif time_interval == "week":
        first_sunday_in_date_range = datetime.strptime(
            f"{first_displayed_date.year}-W{int(first_displayed_date.isocalendar().week )- 2}-1",
            "%Y-W%W-%w",
        ).date()
        fig.update_xaxes(
            range=[
                first_displayed_date,
                max(
                    [
                        datetime.today(),
                        (
                            progress_data[DataSchema.LastLabelDate].max()
                            + timedelta(days=4)
                        ),
                    ]
                ),
            ],
            minor=dict(
                dtick=7 * milliseconds_per_day,
                tick0=first_sunday_in_date_range,
                ticks="inside",
            ),
        )
        fig.update_traces(
            width=7 * milliseconds_per_day,
            customdata=progress_data[["count"]],
            hovertemplate=hovertemplates["week"],
        )
    elif time_interval == "month":
        last_labeled_data_point = progress_data[DataSchema.LastLabelDate].max()
        fig.update_xaxes(
            range=[
                first_displayed_date,
                max(
                    [
                        datetime.today(),
                        datetime(
                            year=last_labeled_data_point.year,
                            month=last_labeled_data_point.month,
                            day=calendar.monthrange(
                                year=last_labeled_data_point.year,
                                month=last_labeled_data_point.month,
                            )[1],
                        ),
                    ]
                ),
            ],
        )
        fig.update_traces(
            width=[
                milliseconds_per_day * days_in_month
                for days_in_month in map(
                    _get_number_of_days_in_month,
                    progress_data[DataSchema.LastLabelDate],
                )
            ],
            customdata=progress_data[["count"]],
            hovertemplate=hovertemplates["month"],
        )
