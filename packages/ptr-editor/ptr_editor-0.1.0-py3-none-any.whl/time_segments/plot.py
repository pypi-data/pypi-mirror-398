"""
Plotting functionalities for time segments.
"""

from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class HasPandas(Protocol):
    """Protocol for objects that can be converted to a pandas DataFrame.

    Any object implementing this protocol must have an as_pandas method
    that returns a pandas DataFrame representation of the object.

    Example:
        >>> class MyData:
        ...     def as_pandas(
        ...         self,
        ...     ) -> (
        ...         pd.DataFrame
        ...     ):
        ...         return pd.DataFrame(
        ...             {
        ...                 "col": [
        ...                     1,
        ...                     2,
        ...                     3,
        ...                 ]
        ...             }
        ...         )
        >>>
        >>> data: HasPandas = (
        ...     MyData()
        ... )  # Type checks!
    """

    def as_pandas(self, **kwargs) -> pd.DataFrame:
        """Convert the object to a pandas DataFrame.

        Returns:
            pd.DataFrame: DataFrame representation of the object
        """
        ...


def plot(obj: HasPandas, height=400, hover_cols=None, **kwargs):
    """Plot the observations in a timeline with plotly.

    Args:
        obj: Object that can be converted to pandas DataFrame
        height: Height of the plot in pixels
        **kwargs: Additional arguments passed to px.timeline()
    """
    import plotly.express as px

    tab = obj.as_pandas().copy()
    tab["timeline"] = "timeline"

    # Set default parameters
    if "timeline" in tab.columns and "y" not in kwargs:
        kwargs["y"] = "timeline"
    if "name" in tab.columns and "color" not in kwargs:
        kwargs["color"] = "name"

    # Include all columns except basic timeline columns in hover data
    excluded_cols = {"start", "end", "timeline"}
    if hover_cols is None:
        hover_cols = [col for col in tab.columns if col not in excluded_cols]

    if hover_cols:
        kwargs["hover_data"] = dict.fromkeys(hover_cols, True)

    # Create the timeline plot with all data in hover
    fig = px.timeline(tab, x_start="start", x_end="end", **kwargs)

    # Let Plotly handle the hover automatically - don't override with custom template
    # The hover_data parameter will ensure all fields are shown correctly

    fig.update_layout(height=height, hovermode="closest")
    return fig
