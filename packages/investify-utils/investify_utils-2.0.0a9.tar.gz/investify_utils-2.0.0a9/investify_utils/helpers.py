"""
Common helper utilities for Investify services.

Usage:
    from investify_utils.helpers import convert_to_pd_timestamp, create_sql_in_filter
"""

import datetime as dt
import importlib.util
import logging
import sys
from numbers import Integral, Number, Real
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# Timestamp Utilities
# =============================================================================


def convert_to_pd_timestamp(timestamp) -> pd.Timestamp | None:
    """
    Convert various timestamp formats to pandas Timestamp.

    Args:
        timestamp: Can be None, pd.Timestamp, number (unix), string, datetime, or np.datetime64

    Returns:
        pd.Timestamp or None
    """
    if timestamp is None:
        return None

    if isinstance(timestamp, pd.Timestamp):
        return timestamp

    if isinstance(timestamp, Number):
        return pd.Timestamp.fromtimestamp(float(timestamp), tz=dt.UTC)

    if isinstance(timestamp, str | dt.datetime | np.datetime64):
        try:
            return pd.Timestamp(timestamp, tzinfo=dt.UTC)
        except Exception as e:
            logger.error(repr(e))
            return timestamp

    return timestamp


# =============================================================================
# SQL Utilities
# =============================================================================


def convert_to_sql_value(value: Integral | Real | str | dt.datetime | dt.date) -> str:
    """
    Convert Python value to SQL literal string.

    Args:
        value: Integer, float, string, datetime, or date

    Returns:
        SQL-safe string representation
    """
    if isinstance(value, Integral):
        value = int(value)
    elif isinstance(value, Real):
        value = float(value)
    elif isinstance(value, str):
        value = f"'{value}'"
    elif isinstance(value, dt.datetime):
        value = value.isoformat(sep=" ")
        value = f"'{value}'"
    elif isinstance(value, dt.date):
        value = value.isoformat()
        value = f"'{value}'"
    else:
        raise ValueError(f"Not supported type={type(value)}")

    return str(value)


def create_sql_in_filter(
    col_name: str,
    values: list[Integral | Real | str | dt.datetime | dt.date],
    not_in: bool = False,
) -> str:
    """
    Create SQL IN or NOT IN filter clause.

    Args:
        col_name: Column name
        values: List of values
        not_in: Use NOT IN instead of IN

    Returns:
        SQL filter string like "col IN (1, 2, 3)"
    """
    operator = "NOT IN" if not_in else "IN"
    values_str = ", ".join([convert_to_sql_value(value) for value in values])
    return f"{col_name} {operator} ({values_str})"


def create_sql_logical_filter(
    filters: list[str],
    operator: Literal["AND", "OR"],
    inner_bracket: bool = False,
    outer_bracket: bool = False,
) -> str:
    """
    Combine multiple SQL filters with AND/OR.

    Args:
        filters: List of filter strings
        operator: "AND" or "OR"
        inner_bracket: Wrap each filter in parentheses
        outer_bracket: Wrap result in parentheses

    Returns:
        Combined filter string
    """
    operator_sep = f" {operator} "
    if inner_bracket:
        filters = [f"({filter})" for filter in filters]
    return f"({operator_sep.join(filters)})" if outer_bracket else operator_sep.join(filters)


# =============================================================================
# Module Utilities
# =============================================================================


def import_module_from_path(file_path: str, module_name: str):
    """
    Dynamically import a Python module from a file path.

    Args:
        file_path: Path to the Python file
        module_name: Name to register the module as

    Returns:
        Imported module object
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    logger.info(f"Loading `{spec.name}` from `{spec.origin}`")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
