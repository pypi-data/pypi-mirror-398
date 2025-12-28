"""
dlt_utils: Shared utilities for dlt data pipelines with multi-company support.

This package provides common utilities for building dlt pipelines that work with
multiple companies/tenants, including:

- PartitionedIncremental: State tracking per partition key
- Date utilities: Generate (year, week) and (year, month) sequences
- Schema utilities: Ensure database tables exist
"""

from .incremental import PartitionedIncremental
from .dates import generate_year_weeks, generate_year_months
from .schema import (
    ensure_all_tables_exist,
    ensure_tables_for_resources,
    get_tables_for_resources,
)

__version__ = "0.1.0"

__all__ = [
    # Incremental
    "PartitionedIncremental",
    # Dates
    "generate_year_weeks",
    "generate_year_months",
    # Schema
    "ensure_all_tables_exist",
    "ensure_tables_for_resources",
    "get_tables_for_resources",
]
