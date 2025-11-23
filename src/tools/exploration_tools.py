"""Data exploration tools for the data agent."""

from datetime import date, datetime
from decimal import Decimal

from src.database.connection import get_db_connection


def serialize_value(value):
    """Convert non-JSON-serializable values to JSON-serializable formats.

    Args:
        value: Any value that might contain date, datetime, or Decimal objects

    Returns:
        JSON-serializable version of the value
    """
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif value is None:
        return None
    else:
        return value


# Table metadata with business descriptions and quality notes
TABLE_METADATA = {
    "customers": {
        "description": "Customer master data including contact information and lifetime value",
        "quality_notes": (
            "Contains intentional quality issues: ~10% missing emails, "
            "~5% missing phones, ~5% duplicate records, ~2% future registration dates, "
            "~2% outliers in lifetime_value"
        ),
    },
    "products": {
        "description": "Product catalog with pricing, inventory, and supplier information",
        "quality_notes": (
            "Contains intentional quality issues: ~8% missing product names, "
            "~1% negative prices, ~3% price outliers, ~2% negative stock quantities"
        ),
    },
    "sales_transactions": {
        "description": "Sales transaction records with customer, product, and payment details",
        "quality_notes": (
            "Contains intentional quality issues: ~2% orphaned customers, "
            "~2% orphaned products, ~1% future dates, ~1% invalid discounts, "
            "~2% calculation errors, ~1% negative quantities, ~5% missing payment methods"
        ),
    },
    "data_quality_metrics": {
        "description": "Historical tracking of data quality metrics over time",
        "quality_notes": "Currently contains 2 initial metrics for completeness and accuracy",
    },
    "pipeline_runs": {
        "description": "Pipeline execution history for data processing jobs",
        "quality_notes": "Currently empty - will be populated when pipelines are executed",
    },
}


def list_tables() -> dict:
    """
    List all available database tables with row counts.

    This tool helps users discover what data is available in the database.
    Returns a list of all tables with their current row counts.

    Returns:
        dict: Status dictionary with tables list
            - status (str): "success" or "error"
            - tables (list): List of dicts with 'name' and 'row_count'
            - total_tables (int): Total number of tables
            - message (str): Helpful description
            - error_message (str): Error details (only if status is "error")

    Example:
        >>> result = list_tables()
        >>> print(result['tables'])
        [{'name': 'customers', 'row_count': 525}, ...]
    """
    try:
        with get_db_connection() as conn:
            # Get all table names
            tables_result = conn.execute("SHOW TABLES").fetchall()

            # Get row count for each table
            tables = []
            for (table_name,) in tables_result:
                count_result = conn.execute(
                    f"SELECT COUNT(*) FROM {table_name}"
                ).fetchone()
                row_count = count_result[0]

                tables.append({"name": table_name, "row_count": row_count})

            # Sort by name for consistency
            tables.sort(key=lambda x: x["name"])

            return {
                "status": "success",
                "tables": tables,
                "total_tables": len(tables),
                "message": f"Found {len(tables)} tables in the database",
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to list tables: {str(e)}",
            "message": "An error occurred while listing database tables",
        }


def describe_table(table_name: str) -> dict:
    """
    Get detailed schema information for a specific table.

    This tool provides the table structure including column names, data types,
    and sample data to help users understand what information the table contains.

    Args:
        table_name (str): Name of the table to describe (case-insensitive)

    Returns:
        dict: Status dictionary with schema and sample data
            - status (str): "success" or "error"
            - table_name (str): Name of the table
            - schema (list): List of dicts with column details
                - column_name (str): Name of the column
                - data_type (str): SQL data type
                - is_nullable (bool): Whether column allows NULL values
            - row_count (int): Total number of rows in table
            - sample_data (list): List of 5 sample rows (as dicts)
            - message (str): Helpful description
            - error_message (str): Error details (only if status is "error")

    Example:
        >>> result = describe_table("customers")
        >>> print(result['schema'])
        [{'column_name': 'customer_id', 'data_type': 'INTEGER', ...}, ...]
    """
    try:
        with get_db_connection() as conn:
            # Normalize table name (case-insensitive)
            table_name_lower = table_name.lower()

            # Check if table exists
            tables_result = conn.execute("SHOW TABLES").fetchall()
            available_tables = [t[0].lower() for t in tables_result]

            if table_name_lower not in available_tables:
                return {
                    "status": "error",
                    "error_message": f"Table '{table_name}' does not exist",
                    "available_tables": [
                        t[0] for t in tables_result
                    ],  # Original case names
                    "message": (
                        f"Table '{table_name}' not found. "
                        "Use list_tables() to see available tables."
                    ),
                }

            # Get the actual table name with correct casing
            actual_table_name = [
                t[0] for t in tables_result if t[0].lower() == table_name_lower
            ][0]

            # Get schema information
            schema_result = conn.execute(f"DESCRIBE {actual_table_name}").fetchall()

            schema = []
            for row in schema_result:
                schema.append(
                    {
                        "column_name": row[0],
                        "data_type": row[1],
                        "is_nullable": row[2] == "YES",
                    }
                )

            # Get row count
            count_result = conn.execute(
                f"SELECT COUNT(*) FROM {actual_table_name}"
            ).fetchone()
            row_count = count_result[0]

            # Get sample data (5 rows)
            sample_result = conn.execute(
                f"SELECT * FROM {actual_table_name} LIMIT 5"
            ).fetchall()

            # Get column names for sample data
            column_names = [col["column_name"] for col in schema]

            # Convert sample rows to list of dicts with serializable values
            sample_data = []
            for row in sample_result:
                row_dict = {
                    col_name: serialize_value(value)
                    for col_name, value in zip(column_names, row)
                }
                sample_data.append(row_dict)

            return {
                "status": "success",
                "table_name": actual_table_name,
                "schema": schema,
                "row_count": row_count,
                "sample_data": sample_data,
                "message": (
                    f"Schema and sample data for '{actual_table_name}' "
                    f"table with {row_count} rows"
                ),
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to describe table '{table_name}': {str(e)}",
            "message": "An error occurred while describing the table",
        }


def get_table_info(table_name: str) -> dict:
    """
    Get comprehensive information about a table including purpose and quality notes.

    This tool provides a complete overview of a table including its business purpose,
    schema, known quality issues, and sample data.

    Args:
        table_name (str): Name of the table to get information about

    Returns:
        dict: Status dictionary with comprehensive table information
            - status (str): "success" or "error"
            - table_name (str): Name of the table
            - description (str): Business purpose of the table
            - schema (list): Column details (name, type, nullable)
            - row_count (int): Total number of rows
            - quality_notes (str): Information about intentional data quality issues
            - sample_data (list): List of 3 sample rows (as dicts)
            - message (str): Helpful description
            - error_message (str): Error details (only if status is "error")

    Example:
        >>> result = get_table_info("products")
        >>> print(result['description'])
        "Product catalog with pricing, inventory, and supplier information"
    """
    try:
        # First get the basic schema and sample data
        describe_result = describe_table(table_name)

        if describe_result["status"] == "error":
            return describe_result

        actual_table_name = describe_result["table_name"]

        # Get metadata from our hardcoded dictionary
        metadata = TABLE_METADATA.get(
            actual_table_name.lower(),
            {
                "description": "No description available",
                "quality_notes": "No quality notes available",
            },
        )

        # Reduce sample data to 3 rows and ensure all values are serializable
        sample_data = []
        for row in describe_result["sample_data"][:3]:
            serialized_row = {k: serialize_value(v) for k, v in row.items()}
            sample_data.append(serialized_row)

        return {
            "status": "success",
            "table_name": actual_table_name,
            "description": metadata["description"],
            "schema": describe_result["schema"],
            "row_count": describe_result["row_count"],
            "quality_notes": metadata["quality_notes"],
            "sample_data": sample_data,
            "message": f"Complete information for '{actual_table_name}' table",
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get table info for '{table_name}': {str(e)}",
            "message": "An error occurred while retrieving table information",
        }
