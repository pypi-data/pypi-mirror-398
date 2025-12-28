from __future__ import annotations
import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta, date
import pandas as pd
from pandas import Timestamp
from pandas.api.typing import NaTType
from easy_image_labeling.helper_functions import TimeIntervals


class DataSchema:
    ImageId = "ImageId"
    Dataset = "Dataset"
    ImageName = "ImageName"
    DatasetID = "DatasetID"
    LabelName = "LabelName"
    LastLabelDate = "LastLabelDate"


@dataclass
class DataSource:
    _data: pd.DataFrame

    @property
    def all_datasets(self) -> list[str]:
        return self._data[DataSchema.Dataset].unique().tolist()

    @property
    def row_count(self) -> int:
        return self._data.shape[0]

    @property
    def last_labeled_date(self) -> datetime:
        return pd.Timestamp(self._data[DataSchema.LastLabelDate].max()).to_pydatetime()

    def filter_by_datasets(self, datasets: list[str]) -> DataSource:
        return DataSource(self._data[self._data[DataSchema.Dataset].isin(datasets)])

    def get_size_of_groups(self, by: str, *other_by: str) -> pd.DataFrame:
        return (
            self._data.groupby([by, *other_by]).size().to_frame("count").reset_index()
        )

    def get_progress_per_time_interval(
        self, time_interval: TimeIntervals
    ) -> pd.DataFrame:
        if time_interval == "day":
            binned_dates = (
                self._data[DataSchema.LastLabelDate]
                .map(convert_date_to_day)
                .rename(DataSchema.LastLabelDate)
            )
        elif time_interval == "week":
            binned_dates = (
                self._data[DataSchema.LastLabelDate]
                .map(convert_date_to_week)
                .rename(DataSchema.LastLabelDate)
            )
        elif time_interval == "month":
            binned_dates = (
                self._data[DataSchema.LastLabelDate]
                .map(convert_date_to_month)
                .rename(DataSchema.LastLabelDate)
            )
        else:
            raise NotImplementedError
        return binned_dates.value_counts(dropna=True).to_frame().reset_index()


def convert_date_to_day(date: Timestamp | NaTType) -> date | NaTType:
    """
    Map date string to date object.
    """

    if isinstance(date, NaTType):
        return date
    return date.date()


def convert_date_to_week(date: Timestamp | NaTType) -> date | NaTType:
    """
    Map date string to date string of middle of that original date
    strings week.
    """

    if isinstance(date, NaTType):
        return date
    date_dt = date.date()
    year = date_dt.year
    week = date_dt.isocalendar().week
    first_day_of_week = datetime.strptime(f"{year}-W{int(week )- 1}-1", r"%Y-W%W-%w")
    middle_day_of_week = first_day_of_week + timedelta(days=3)
    return middle_day_of_week


def convert_date_to_month(date: Timestamp | NaTType) -> date | NaTType:
    """
    Map date string to date string of first day of that original date
    strings month.
    """

    if isinstance(date, NaTType):
        return date
    date_dt = date.date()
    year = date_dt.year
    month = date_dt.month
    first_day_of_month = datetime.strptime(f"{year}-{int(month)}", r"%Y-%m")
    return first_day_of_month
