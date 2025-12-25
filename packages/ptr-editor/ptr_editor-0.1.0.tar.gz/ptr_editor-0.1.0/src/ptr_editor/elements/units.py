"""Units that can be used in the PTR file."""

from typing import Literal

ANGULAR_UNITS_LITERAL = Literal["deg", "rad", "arcMin", "arcSec"]
DELTA_TIME_UNITS_LITERAL = Literal["sec", "min", "hour", "day", "dhms"]
DISTANCE_UNITS_LITERAL = Literal["km", "m"]
ANGULAR_VELOCITY_UNITS_LITERAL = Literal[
    "deg/sec",
    "rad/sec",
    "arcMin/sec",
    "arcSec/sec",
    "deg/min",
    "rad/min",
    "arcMin/min",
    "arcSec/min",
    "deg/hour",
    "rad/hour",
    "arcMin/hour",
    "arcSec/hour",
]


def print_known_units() -> None:
    """Print all supported units."""
    print("Supported angular units:")
    for unit in ANGULAR_UNITS_LITERAL.__args__:
        print(f" - {unit}")

    print("\nSupported delta time units:")
    for unit in DELTA_TIME_UNITS_LITERAL.__args__:
        print(f" - {unit}")

    print("\nSupported distance units:")
    for unit in DISTANCE_UNITS_LITERAL.__args__:
        print(f" - {unit}")

    print("\nSupported angular velocity units:")
    for unit in ANGULAR_VELOCITY_UNITS_LITERAL.__args__:
        print(f" - {unit}")