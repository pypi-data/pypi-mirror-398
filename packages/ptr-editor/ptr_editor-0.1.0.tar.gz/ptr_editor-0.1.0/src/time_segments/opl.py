"""IO and other utilities for OPL files."""

from pathlib import Path

import pandas as pd
from loguru import logger as log

from .config import config


def load_opl_as_pandas_table(filename: str | Path, skiprows=0) -> pd.DataFrame:
    """Load an OPL file as a pandas table."""
    return pd.read_csv(filename, names=config.OPL_DEFAULT_COLUMNS, skiprows=skiprows)


def set_default_opl_columns(table: pd.DataFrame) -> pd.DataFrame:
    """Set the default columns for a valid OPL if they are not present."""
    for col_name in config.OPL_DEFAULT_COLUMNS:
        if col_name not in table.columns or table[col_name].isnull().all():
            def_value = getattr(config, f"OPL_DEFAULT_{col_name.upper()}")
            log.warning(
                f"Column {col_name} is empty or non-existent. Filling with default value: {def_value}",
            )

            table[col_name] = def_value

    return table


def ensure_opl_columns(table: pd.DataFrame) -> pd.DataFrame:
    """Ensure that the table has the correct columns for OPL."""
    if not set(config.OPL_DEFAULT_COLUMNS).issubset(set(table.columns)):
        log.warning(
            f"Table must have the following columns: {config.OPL_DEFAULT_COLUMNS}."
            f" Columns found: {table.columns}.",
        )

        set_default_opl_columns(table)

    return table


def save_pandas_table_as_opl(
    table: pd.DataFrame,
    filename: str | Path,
    overwrite: bool = False,
    columns_rename: dict | None = None,
) -> None:
    """
    Save a pandas table as an OPL file.

    The table must have the following columns: segment_definition, start, end, name, timeline.
    If not you can specify the columns name remapping with the columns_rename argument.
    """
    if columns_rename is None:
        columns_rename = {}
    if Path(filename).exists() and not overwrite:
        msg = f"File {filename} exists. Set overwrite=True to overwrite."
        raise FileExistsError(msg)

    if columns_rename:
        table = table.rename(columns=columns_rename)

    table = ensure_opl_columns(table)

    subtable = pandas_table_to_opl_subset(table, columns_rename=columns_rename)

    subtable.to_csv(filename, header=False, index=False, date_format="%Y-%m-%dT%H:%M:%S.%fZ")
    return subtable


def pandas_table_to_opl_subset(
    table: pd.DataFrame, columns_rename: dict | None = None,
) -> pd.DataFrame:
    """
    Return a subset of the table with only the columns needed for OPL in the right order.

    The table must have the following columns: segment_definition, start, end, name, timeline.
    If not you can specify the columns name remapping with the columns_rename argument.
    """
    if columns_rename is None:
        columns_rename = {}
    if columns_rename:
        table = table.rename(columns=columns_rename)

    def format_time(t):
        return t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    table.start = table.start.apply(format_time)
    table.end = table.end.apply(format_time)

    return table[config.OPL_DEFAULT_COLUMNS]
