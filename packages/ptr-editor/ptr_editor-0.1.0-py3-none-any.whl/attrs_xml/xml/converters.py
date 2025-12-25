import datetime

import pandas as pd

UTC = datetime.UTC


def format_timestamp(timestamp: pd.Timestamp) -> str:
    """
    Format a pandas Timestamp to the string format yyyy-mm-ddThh:mm:ss[.sss][Z].

    Args:
        timestamp (pd.Timestamp): The timestamp to format.

    Returns:
        str: The formatted timestamp string.
    """
    if not isinstance(timestamp, pd.Timestamp):
        msg = "Input must be a pandas Timestamp."
        raise TypeError(msg)

    if timestamp.tz is not None:
        was_localized = True

    if not timestamp.tz:
        was_localized = False
        timestamp = timestamp.tz_localize(UTC)

    if timestamp.tz != UTC:
        timestamp = timestamp.tz_convert(UTC)

    timestamp = timestamp.tz_localize(
        None,
    )  # strip away localization to then get a correct isoformat as we need.
    postfix = "Z" if was_localized else ""

    # Use isoformat with milliseconds precision only if needed
    timespec = "seconds" if timestamp.microsecond == 0 else "milliseconds"
    # Ensure UTC handling and isolate fractional seconds
    return timestamp.isoformat(timespec=timespec) + postfix



def to_timestamp(value: pd.Timestamp | str) -> pd.Timestamp:
    if isinstance(value, pd.Timestamp):
        return value
    if isinstance(value, str):
        return pd.Timestamp(value)
    msg = f"Unsupported type for time value {type(value)}"
    raise TypeError(msg)


def encode_bool(value: bool) -> str:
    return "true" if value else "false"


def decode_bool(value: str | bool) -> bool:
    if isinstance(value, str):
        return value.lower().strip() == "true"
    if isinstance(value, bool):
        return value

    return False
