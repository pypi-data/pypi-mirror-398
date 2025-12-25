from numpy import isin
import pandas as pd

from attrs_xml.xml.converter import make_default_xml_converter
from attrs_xml.xml.utils import remove_null_values
from ptr_editor.io.ptr_converter_setup import setup_subclasses_disambiguation
from ptr_editor.elements.array import VectorWithUnits
from ptr_editor.elements.blocks import Block
from ptr_editor.elements.directions import (
    Direction,
    VectorDirection,
)
from ptr_editor.elements.values import ValueWithUnits

from ptr_editor.elements.blocks import SlewBlock

from ptr_editor.elements.metadata import Observations

conv = make_default_xml_converter(rename=False)


conv.register_unstructure_hook(Direction, str)
conv.register_unstructure_hook(ValueWithUnits, str)
conv.register_unstructure_hook(VectorWithUnits, str)
conv.register_unstructure_hook(VectorDirection, str)


def _unstructure_observations(obj: Observations) -> list[str]:
    return [obs.obs_id for obs in obj.observations]

conv.register_unstructure_hook(Observations, _unstructure_observations)


setup_subclasses_disambiguation(conv)


def tabletize_block(
    obj: Block,
    *,
    attrs: list[str] | None = None,
    priority_columns: list[str] | None = None,
    add_xml: bool = False,
) -> pd.Series:
    """Convert a Block object to a pandas Series with optional attribute extraction.

    Args:
        obj: The Block object to convert
        attrs: Optional list of additional attribute names to extract from the object.
            These will be added as columns in the resulting Series.
        priority_columns: Optional list of column names that should appear first
            in the Series. Defaults to ["id", "start", "end", "designer"].

    Returns:
        pd.Series with the block data, with priority columns ordered first.

    Example:
        >>> series = tabletize_block(
        ...     block,
        ...     attrs=[
        ...         "id",
        ...         "designer",
        ...         "custom_field",
        ...     ],
        ... )
    """
    # Convert block to dict and normalize
    data = conv.unstructure(obj)
    data = remove_null_values(data)
    astable = pd.json_normalize(data, sep=".")
    
    series: pd.Series |str = astable.squeeze(axis=0)
    


    # Extract additional attributes if specified
    if attrs:
        for attr_name in attrs:
            series[attr_name] = getattr(obj, attr_name, None)

    # Reorder columns to ensure priority columns appear first
    if priority_columns is None:
        priority_columns = ["id", "start", "end", "designer"]

    # Find which priority columns actually exist in the series
    existing_priority = [col for col in priority_columns if col in series.index]

    # Get all other columns
    other_columns = [col for col in series.index if col not in priority_columns]

    # Reorder: priority columns first, then everything else
    column_order = existing_priority + other_columns

    if add_xml:
        series['xml'] = obj.xml

    return series[column_order]
