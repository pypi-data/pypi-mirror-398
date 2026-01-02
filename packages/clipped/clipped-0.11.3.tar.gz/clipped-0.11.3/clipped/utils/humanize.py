from datetime import datetime
from typing import Any, Union

from clipped.utils.dates import DateTimeFormatter, parse_datetime
from clipped.utils.json import orjson_dumps
from clipped.utils.tz import now
from clipped.utils.units import to_percentage, to_unit_memory


def humanize_timestamp(
    timestamp: Union[str, datetime],
) -> str:
    if not timestamp:
        return timestamp

    timestamp = parse_datetime(timestamp)
    return DateTimeFormatter.format_datetime(timestamp)


def humanize_timesince(
    timesince: Union[str, datetime],
) -> str:  # pylint:disable=too-many-return-statements
    """Creates a string representation of time since the given `start_time`."""
    if not timesince:
        return timesince

    start_time = parse_datetime(timesince)

    delta = now() - start_time

    # assumption: negative delta values originate from clock
    #             differences on different app server machines
    if delta.total_seconds() < 0:
        return "a few seconds ago"

    num_years = delta.days // 365
    if num_years > 0:
        return "{} year{} ago".format(
            *((num_years, "s") if num_years > 1 else (num_years, ""))
        )

    num_weeks = delta.days // 7
    if num_weeks > 0:
        return "{} week{} ago".format(
            *((num_weeks, "s") if num_weeks > 1 else (num_weeks, ""))
        )

    num_days = delta.days
    if num_days > 0:
        return "{} day{} ago".format(
            *((num_days, "s") if num_days > 1 else (num_days, ""))
        )

    num_hours = delta.seconds // 3600
    if num_hours > 0:
        return "{} hour{} ago".format(
            *((num_hours, "s") if num_hours > 1 else (num_hours, ""))
        )

    num_minutes = delta.seconds // 60
    if num_minutes > 0:
        return "{} minute{} ago".format(
            *((num_minutes, "s") if num_minutes > 1 else (num_minutes, ""))
        )

    return "a few seconds ago"


def humanize_timedelta(seconds: int) -> str:
    """Creates a string representation of timedelta."""
    hours, remainder = divmod(seconds, 3600)
    days, hours = divmod(hours, 24)
    minutes, seconds = divmod(remainder, 60)

    if days:
        result = "{}d".format(days)
        if hours:
            result += " {}h".format(hours)
        if minutes:
            result += " {}m".format(minutes)
        return result

    if hours:
        result = "{}h".format(hours)
        if minutes:
            result += " {}m".format(minutes)
        return result

    if minutes:
        result = "{}m".format(minutes)
        if seconds:
            result += " {}s".format(seconds)
        return result

    return "{}s".format(seconds)


def humanize_attrs(
    key: str, value: Any, rounding: int = 2, timesince: bool = True
) -> str:
    if key in [
        "created_at",
        "updated_at",
        "started_at",
        "finished_at",
        "schedule_at",
        "last_update_time",
        "last_transition_time",
    ]:
        if timesince:
            return humanize_timesince(value)
        return humanize_timestamp(value)
    if key in ["cpu_percentage"]:
        return to_percentage(value, rounding)
    if key in ["memory_free", "memory_used", "memory_total"]:
        return to_unit_memory(value)
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return orjson_dumps(value)
