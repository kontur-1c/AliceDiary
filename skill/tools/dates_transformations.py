import datetime

from dateutil import relativedelta


def adjust_relative_dates(
    *, initial_date: datetime.datetime, yandex_dict: dict
) -> datetime.datetime:
    if "value" in yandex_dict:
        yandex_dict = yandex_dict["value"]
    relative_year = (
        yandex_dict["year"]
        if (
            "year_is_relative" in yandex_dict
            and yandex_dict["year_is_relative"] is True
        )
        else 0
    )

    relative_month = (
        yandex_dict["month"]
        if (
            "month_is_relative" in yandex_dict
            and yandex_dict["month_is_relative"] is True
        )
        else 0
    )

    relative_day = (
        yandex_dict["day"]
        if ("day_is_relative" in yandex_dict and yandex_dict["day_is_relative"] is True)
        else 0
    )

    relative_hour = (
        yandex_dict["hour"]
        if (
            "hour_is_relative" in yandex_dict
            and yandex_dict["hour_is_relative"] is True
        )
        else 0
    )

    relative_minute = (
        yandex_dict["minute"]
        if (
            "minute_is_relative" in yandex_dict
            and yandex_dict["minute_is_relative"] is True
        )
        else 0
    )

    relative_second = (
        yandex_dict["second"]
        if (
            "second_is_relative" in yandex_dict
            and yandex_dict["second_is_relative"] is True
        )
        else 0
    )
    return initial_date + relativedelta.relativedelta(
        years=relative_year,
        months=relative_month,
        days=relative_day,
        hours=relative_hour,
        minutes=relative_minute,
        seconds=relative_second,
    )


def adjust_absolute_dates(
    *, initial_date: datetime.datetime, yandex_dict: dict
) -> datetime.datetime:
    if "value" in yandex_dict:
        yandex_dict = yandex_dict["value"]
    adjusted_date = initial_date
    if "year_is_relative" in yandex_dict and yandex_dict["year_is_relative"] is False:
        adjusted_date = adjusted_date.replace(year=yandex_dict["year"])

    if "month_is_relative" in yandex_dict and yandex_dict["month_is_relative"] is False:
        adjusted_date = adjusted_date.replace(month=yandex_dict["month"])

    if "day_is_relative" in yandex_dict and yandex_dict["day_is_relative"] is False:
        adjusted_date = adjusted_date.replace(day=yandex_dict["day"])

    if "hour_is_relative" in yandex_dict and yandex_dict["hour_is_relative"] is False:
        adjusted_date = adjusted_date.replace(hour=yandex_dict["hour"])

    if (
        "minute_is_relative" in yandex_dict
        and yandex_dict["minute_is_relative"] is False
    ):
        adjusted_date = adjusted_date.replace(minute=yandex_dict["minute"])

    if (
        "second_is_relative" in yandex_dict
        and yandex_dict["second_is_relative"] is False
    ):
        adjusted_date = adjusted_date.replace(second=yandex_dict["second"])

    return adjusted_date


def transform_yandex_datetime_value_to_datetime(
    yandex_datetime_value_dict,
) -> datetime.datetime:
    return adjust_absolute_dates(
        initial_date=adjust_relative_dates(
            initial_date=datetime.datetime.now(), yandex_dict=yandex_datetime_value_dict
        ),
        yandex_dict=yandex_datetime_value_dict,
    )
