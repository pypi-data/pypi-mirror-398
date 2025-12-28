import calendar
from datetime import date
from pathlib import Path
from typing import Literal, get_args

TimeIntervals = Literal["day", "week", "month"]

TimeIntervals_args = get_args(TimeIntervals)


def create_env_file_with_provided_key():
    """
    Ask user to provide secret key. If valid key is entered create
    secret.env file and write key into it.
    """

    secret_key = input("Enter secret key:\n")
    if "" == secret_key:
        raise ValueError("Secret key is empty!")
    if " " in secret_key:
        raise ValueError("No whitespaces allowed!")
    if "\n" in secret_key:
        raise ValueError("No newline characters allowed!")
    with open(Path(__file__).parent.parent / "secret.env", "w") as f:
        f.write(secret_key)
    print("Successfully created secret.env file!")


def _get_number_of_days_in_month(date: date) -> int:
    """
    Return number of days in month that the specified date belongs to.
    """

    return calendar.monthrange(year=date.year, month=date.month)[1]
