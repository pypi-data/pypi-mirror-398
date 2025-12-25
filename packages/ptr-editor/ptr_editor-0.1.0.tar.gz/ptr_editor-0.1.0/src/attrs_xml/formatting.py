import re

import pandas as pd


def format_timedelta_to_hhmmss(td: pd.Timedelta) -> str:
    """
    Formats a pandas Timedelta object into a string with a sign and HH:MM:SS.mmm format.

    Args:
        td (pd.Timedelta): The Timedelta object to format.

    Returns:
        str: The formatted timedelta string (e.g., '+00:00:00.123', '-00:30:00.456').
    """
    if not isinstance(td, pd.Timedelta):
        msg = "Input must be a pandas Timedelta object."
        raise TypeError(msg)

    # Determine the sign
    sign = "+"
    if td < pd.Timedelta(0):
        sign = "-"
        td = abs(td)  # Work with the absolute value for formatting

    # Convert timedelta to total seconds and milliseconds
    total_seconds = int(td.total_seconds())
    milliseconds = int(td.microseconds // 1000)

    # Calculate hours, minutes, and seconds from the total seconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Format each component with leading zeros to ensure two digits, ms to three digits
    formatted_hours = f"{hours:02d}"
    formatted_minutes = f"{minutes:02d}"
    formatted_seconds = f"{seconds:02d}"
    formatted_milliseconds = f"{milliseconds:03d}"

    asstring = f"{sign}{formatted_hours}:{formatted_minutes}:{formatted_seconds}"

    # add milliseconds only if needed
    if milliseconds != 0:
        asstring += f".{formatted_milliseconds}"

    # Construct the final string with milliseconds
    return asstring


def parse_delta_time_string(delta_str: str | pd.Timedelta) -> pd.Timedelta:
    """
    Parse a delta_time string in OPL format to pandas Timedelta.
    
    Supports formats:
    - [+-]ddd.hh:mm:ss[.SSS]  (with days, e.g., "+0.00:30:00.000")
    - [+-]hh:mm:ss[.SSS]      (without days, e.g., "-00:30:00.456")
    
    Args:
        delta_str (str | pd.Timedelta): The delta time string to parse, or an already
            parsed pd.Timedelta object.
        
    Returns:
        pd.Timedelta: The parsed timedelta object.
        
    Raises:
        ValueError: If the string format is invalid.
        
    Examples:
        >>> parse_delta_time_string("+0.00:30:00.000")
        Timedelta('0 days 00:30:00')
        >>> parse_delta_time_string("-0.12:45:30.500")
        Timedelta('-1 days +11:14:29.500000')
    """
    # If already a Timedelta, return it
    if isinstance(delta_str, pd.Timedelta):
        return delta_str
    
    if not isinstance(delta_str, str):
        msg = f"Input must be a string or pd.Timedelta, got {type(delta_str)}"
        raise TypeError(msg)
    
    delta_str = delta_str.strip()
    
    # Pattern: [+-]ddd.hh:mm:ss[.SSS] or [+-]hh:mm:ss[.SSS]
    # The schema pattern is: ^[+-]?\d{1,3}\.\d{1,2}:\d{2}:\d{2}(\.\d{1,3})?$
    pattern = r'^([+-])?(?:(\d{1,3})\.)?(\d{1,2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?$'
    match = re.match(pattern, delta_str)
    
    if not match:
        msg = (
            f"Invalid delta_time format: '{delta_str}'. "
            f"Expected format: [+-]ddd.hh:mm:ss[.SSS] or [+-]hh:mm:ss[.SSS]"
        )
        raise ValueError(msg)
    
    sign_str, days_str, hours_str, minutes_str, seconds_str, millis_str = match.groups()
    
    # Parse components
    sign = -1 if sign_str == "-" else 1
    days = int(days_str) if days_str else 0
    hours = int(hours_str)
    minutes = int(minutes_str)
    seconds = int(seconds_str)
    milliseconds = int(millis_str) if millis_str else 0
    
    # Convert to total timedelta
    td = pd.Timedelta(
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        milliseconds=milliseconds,
    )
    
    return sign * td


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case string to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def to_snake_case(camel_str: str) -> str:
    """Convert camelCase string to snake_case."""
    # Insert an underscore before any uppercase letter that follows a lowercase letter or digit
    snake_str = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", camel_str)
    return snake_str.lower()
