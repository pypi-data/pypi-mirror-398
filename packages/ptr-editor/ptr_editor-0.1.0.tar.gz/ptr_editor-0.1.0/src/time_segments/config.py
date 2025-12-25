"""Hosts some configurables for the planning module."""


from attr import define, field


@define
class Config:
    """Configurable values for the planning module."""

    OPL_DEFAULT_COLUMNS: list[str] = field(
        default=["segment_definition", "start", "end", "name", "timeline"],
    )
    OPL_DEFAULT_SEGMENT_DEFINITION: str = field(default="JANUS_PRIME_OBSERVATION")
    OPL_DEFAULT_NAME: str = field(default="OBS")
    OPL_DEFAULT_TIMELINE: str = field(default="JANUS")
    DEFAULT_TRAJECTORY: str = field(default="5_1_150lb_23_1_a3")


config = Config()
