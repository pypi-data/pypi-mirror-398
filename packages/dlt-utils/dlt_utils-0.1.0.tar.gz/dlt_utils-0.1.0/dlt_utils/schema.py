"""
Schema utilities for dlt pipelines.

Provides functions to ensure database tables exist before running pipelines,
which is useful for scenarios where you need tables created without data load.
"""

import logging
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from dlt import Pipeline

logger = logging.getLogger(__name__)


def ensure_all_tables_exist(
    pipeline: "Pipeline",
    only_tables: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """
    Ensure all tables from the schema exist in the database.

    Uses dlt's own SQL generation and executes CREATE TABLE statements for
    tables that don't exist yet.

    IMPORTANT: This bypasses dlt's schema hash check, so tables are created
    even if the schema appears "up to date".

    Args:
        pipeline: An initialized dlt pipeline with a loaded schema.
        only_tables: Optional - only create these specific tables.

    Returns:
        Dict with info about created tables (schema_update).

    Example:
        ```python
        pipeline = dlt.pipeline(
            pipeline_name="my_pipeline",
            destination="postgres",
            dataset_name="my_dataset",
        )

        # Load schema from file or run once
        pipeline.run(my_source().with_resources("__nothing__"))

        # Now ensure all tables exist
        ensure_all_tables_exist(pipeline)
        ```
    """
    tables_to_check = (
        list(only_tables) if only_tables else list(pipeline.default_schema.tables.keys())
    )

    with pipeline.destination_client() as client:
        # Get existing tables from the database
        # get_storage_tables returns (table_name, columns_dict) tuples
        storage_tables = list(client.get_storage_tables(tables_to_check))

        # Build CREATE/ALTER statements
        sql_scripts, schema_update = client._build_schema_update_sql(storage_tables)

        if sql_scripts:
            logger.info(f"Executing {len(sql_scripts)} SQL statements to create/update tables")
            for sql in sql_scripts:
                logger.debug(f"SQL: {sql[:100]}...")

            # Execute the SQL
            client.sql_client.execute_many(sql_scripts)

            logger.info(f"Created/updated {len(schema_update)} tables: {list(schema_update.keys())}")
        else:
            logger.info("All tables already exist and are up to date")

        return schema_update or {}


def get_tables_for_resources(
    pipeline: "Pipeline",
    resource_names: List[str],
) -> List[str]:
    """
    Find all tables (root + children) for given resources.

    This is useful when you need to know which tables will be created
    for a set of resources, including nested/child tables.

    Args:
        pipeline: An initialized dlt pipeline with a loaded schema.
        resource_names: List of resource names to find tables for.

    Returns:
        List of table names including child tables.

    Example:
        ```python
        tables = get_tables_for_resources(pipeline, ["trade_items"])
        # Returns: ["trade_items", "trade_items__photos", "trade_items__characteristics", ...]
        ```
    """
    schema = pipeline.default_schema
    tables = schema.tables

    relevant_tables = set()

    for resource_name in resource_names:
        # Root table
        if resource_name in tables:
            relevant_tables.add(resource_name)

        # Child tables (tables with parent relation or matching prefix)
        for table_name, table_def in tables.items():
            # Check prefix (common pattern for nested tables)
            if table_name.startswith(f"{resource_name}__"):
                relevant_tables.add(table_name)

            # Or via parent chain
            parent = table_def.get("parent")
            checked = set()
            while parent and parent not in checked:
                checked.add(parent)
                if parent == resource_name:
                    relevant_tables.add(table_name)
                    break
                parent = tables.get(parent, {}).get("parent")

    return list(relevant_tables)


def ensure_tables_for_resources(
    pipeline: "Pipeline",
    resource_names: List[str],
) -> Dict[str, Any]:
    """
    Ensure tables exist for specific resources (including child tables).

    Combines get_tables_for_resources and ensure_all_tables_exist for
    convenient resource-based table creation.

    Args:
        pipeline: An initialized dlt pipeline with a loaded schema.
        resource_names: List of resource names to ensure tables for.

    Returns:
        Dict with info about created tables.

    Example:
        ```python
        # Only create tables for trade_items and organizations
        ensure_tables_for_resources(pipeline, ["trade_items", "organizations"])
        ```
    """
    tables = get_tables_for_resources(pipeline, resource_names)
    logger.info(f"Ensuring {len(tables)} tables exist for resources {resource_names}")

    return ensure_all_tables_exist(pipeline, only_tables=tables)
