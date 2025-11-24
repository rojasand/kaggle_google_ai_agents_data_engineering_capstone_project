"""Quality indicators tools for querying data quality metrics."""

from datetime import date

from src.database.connection import get_db_connection
from src.tools.exploration_tools import serialize_value


def get_quality_metrics_by_scope_date(scope_date: str) -> dict:
    """
    Get all quality metrics for a specific scope_date.

    This tool retrieves all data quality metrics calculated for data
    ingested on a specific date, helping identify which days had quality issues.

    Args:
        scope_date (str): The scope date to query in YYYY-MM-DD format (e.g., "2024-11-24")

    Returns:
        dict: Status dictionary with quality metrics
            - status (str): "success" or "error"
            - scope_date (str): The queried scope date
            - metrics (list): List of quality metric records
                - metric_id (int): Unique metric identifier
                - table_name (str): Table being measured
                - metric_name (str): Type of metric
                - metric_value (float): Metric score (0-1)
                - calculation_date (str): When metric was calculated
                - logic_date (str): Date for which data is measured
                - status (str): Calculation status
            - total_metrics (int): Number of metrics found
            - message (str): Helpful description
            - error_message (str): Error details (only if status is "error")

    Example:
        >>> result = get_quality_metrics_by_scope_date("2024-11-24")
        >>> print(result['metrics'])
        [{'metric_id': 1, 'table_name': 'customers', ...}, ...]
    """
    try:
        # Validate date format
        try:
            date.fromisoformat(scope_date)
        except ValueError:
            return {
                "status": "error",
                "error_message": f"Invalid date format: '{scope_date}'. Expected YYYY-MM-DD",
                "message": "Please provide date in YYYY-MM-DD format (e.g., '2024-11-24')",
            }

        with get_db_connection() as conn:
            # Query metrics for the given scope_date (using logic_date)
            result = conn.execute(
                """
                SELECT 
                    metric_id, table_name, metric_name, metric_value,
                    calculation_date, logic_date, status
                FROM data_quality_metrics
                WHERE logic_date = ?
                ORDER BY calculation_date DESC, table_name, metric_name
            """,
                [scope_date],
            ).fetchall()

            # Convert to list of dicts with serialized values
            metrics = []
            for row in result:
                metric = {
                    "metric_id": row[0],
                    "table_name": row[1],
                    "metric_name": row[2],
                    "metric_value": serialize_value(row[3]),
                    "calculation_date": serialize_value(row[4]),
                    "logic_date": serialize_value(row[5]),
                    "status": row[6],
                }
                metrics.append(metric)

            if not metrics:
                return {
                    "status": "success",
                    "scope_date": scope_date,
                    "metrics": [],
                    "total_metrics": 0,
                    "message": f"No quality metrics found for scope_date: {scope_date}",
                }

            return {
                "status": "success",
                "scope_date": scope_date,
                "metrics": metrics,
                "total_metrics": len(metrics),
                "message": f"Found {len(metrics)} quality metrics for scope_date: {scope_date}",
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to query quality metrics: {str(e)}",
            "message": "An error occurred while querying quality metrics",
        }


def get_quality_metrics_by_table(table_name: str, scope_date: str | None = None) -> dict:
    """
    Get quality metrics for a specific table, optionally filtered by scope_date.

    This tool retrieves quality metrics for a specific table, showing the quality
    indicators over time or for a specific date.

    Args:
        table_name (str): Name of the table to query metrics for
        scope_date (str | None): Optional scope date in YYYY-MM-DD format.
                                  If None, returns all metrics for the table.

    Returns:
        dict: Status dictionary with quality metrics
            - status (str): "success" or "error"
            - table_name (str): The queried table name
            - scope_date (str | None): The scope date filter (if provided)
            - metrics (list): List of quality metric records
            - total_metrics (int): Number of metrics found
            - message (str): Helpful description
            - error_message (str): Error details (only if status is "error")

    Example:
        >>> result = get_quality_metrics_by_table("customers", "2024-11-24")
        >>> print(result['metrics'])
        [{'metric_id': 1, 'metric_name': 'completeness', ...}, ...]
    """
    try:
        # Validate date format if provided
        if scope_date:
            try:
                date.fromisoformat(scope_date)
            except ValueError:
                return {
                    "status": "error",
                    "error_message": f"Invalid date format: '{scope_date}'. Expected YYYY-MM-DD",
                    "message": "Please provide date in YYYY-MM-DD format (e.g., '2024-11-24')",
                }

        with get_db_connection() as conn:
            # Build query based on whether scope_date is provided
            if scope_date:
                result = conn.execute(
                    """
                    SELECT 
                        metric_id, table_name, metric_name, metric_value,
                        calculation_date, logic_date, status
                    FROM data_quality_metrics
                    WHERE table_name = ? AND logic_date = ?
                    ORDER BY calculation_date DESC, metric_name
                """,
                    [table_name, scope_date],
                ).fetchall()
            else:
                result = conn.execute(
                    """
                    SELECT 
                        metric_id, table_name, metric_name, metric_value,
                        calculation_date, logic_date, status
                    FROM data_quality_metrics
                    WHERE table_name = ?
                    ORDER BY logic_date DESC, calculation_date DESC, metric_name
                """,
                    [table_name],
                ).fetchall()

            # Convert to list of dicts with serialized values
            metrics = []
            for row in result:
                metric = {
                    "metric_id": row[0],
                    "table_name": row[1],
                    "metric_name": row[2],
                    "metric_value": serialize_value(row[3]),
                    "calculation_date": serialize_value(row[4]),
                    "logic_date": serialize_value(row[5]),
                    "status": row[6],
                }
                metrics.append(metric)

            if not metrics:
                if scope_date:
                    msg = f"No quality metrics found for table '{table_name}' on {scope_date}"
                else:
                    msg = f"No quality metrics found for table '{table_name}'"

                return {
                    "status": "success",
                    "table_name": table_name,
                    "scope_date": scope_date,
                    "metrics": [],
                    "total_metrics": 0,
                    "message": msg,
                }

            if scope_date:
                msg = f"Found {len(metrics)} quality metrics for '{table_name}' on {scope_date}"
            else:
                msg = f"Found {len(metrics)} quality metrics for '{table_name}'"

            return {
                "status": "success",
                "table_name": table_name,
                "scope_date": scope_date,
                "metrics": metrics,
                "total_metrics": len(metrics),
                "message": msg,
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to query quality metrics: {str(e)}",
            "message": "An error occurred while querying quality metrics",
        }


def list_available_scope_dates() -> dict:
    """
    List all unique scope_dates that have quality metrics.

    This tool helps discover which dates have quality metrics available,
    useful for time-series analysis of data quality.

    Returns:
        dict: Status dictionary with available scope dates
            - status (str): "success" or "error"
            - scope_dates (list): List of unique scope dates (sorted desc)
            - total_dates (int): Number of unique dates
            - message (str): Helpful description
            - error_message (str): Error details (only if status is "error")

    Example:
        >>> result = list_available_scope_dates()
        >>> print(result['scope_dates'])
        ['2024-11-24', '2024-11-23', '2024-11-22']
    """
    try:
        with get_db_connection() as conn:
            result = conn.execute(
                """
                SELECT DISTINCT logic_date
                FROM data_quality_metrics
                ORDER BY logic_date DESC
            """
            ).fetchall()

            scope_dates = [serialize_value(row[0]) for row in result]

            if not scope_dates:
                return {
                    "status": "success",
                    "scope_dates": [],
                    "total_dates": 0,
                    "message": "No quality metrics found in the database",
                }

            return {
                "status": "success",
                "scope_dates": scope_dates,
                "total_dates": len(scope_dates),
                "message": f"Found quality metrics for {len(scope_dates)} unique dates",
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to list scope dates: {str(e)}",
            "message": "An error occurred while listing available scope dates",
        }
