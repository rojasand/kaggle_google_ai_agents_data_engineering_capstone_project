"""Quality indicators tools for querying data quality metrics."""

from datetime import date, datetime
from decimal import Decimal

import polars as pl

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
            ).fetchall()  # Convert to list of dicts with serialized values
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


def calculate_quality_metrics(
    table_name: str, logic_date: str | None = None, metric_types: list[str] | None = None
) -> dict:
    """
    Calculate data quality metrics for a specific table on a given logic_date.

    This tool uses Polars to calculate various quality indicators (completeness,
    accuracy, validity, integrity, consistency, uniqueness) from database tables,
    then updates the data_quality_metrics table with the calculated values.

    Args:
        table_name (str): Name of the table to calculate metrics for.
                         Valid values: "customers", "products", "sales_transactions"
        logic_date (str | None): The scope date to calculate metrics for in YYYY-MM-DD format.
                                 If None, uses today's date.
        metric_types (list[str] | None): Specific metric types to calculate.
                                        If None, calculates all available metrics for the table.
                                        Example: ["completeness_email", "validity_unit_price"]

    Returns:
        dict: Status dictionary with calculation results
            - status (str): "success" or "error"
            - table_name (str): The table that was analyzed
            - logic_date (str): The date for which metrics were calculated
            - metrics_calculated (list): List of calculated metrics with names and values
            - total_metrics (int): Number of metrics calculated
            - message (str): Helpful description
            - error_message (str): Error details (only if status is "error")

    Example:
        >>> result = calculate_quality_metrics("customers", "2024-11-24")
        >>> print(result['metrics_calculated'])
        [{'metric_name': 'completeness_email', 'metric_value': 0.90}, ...]
    """
    try:
        # Validate table name
        valid_tables = ["customers", "products", "sales_transactions"]
        if table_name not in valid_tables:
            return {
                "status": "error",
                "error_message": (
                    f"Invalid table name: '{table_name}'. Must be one of {valid_tables}"
                ),
                "message": f"Please provide a valid table name: {', '.join(valid_tables)}",
            }

        # Use today's date if logic_date not provided
        if logic_date is None:
            logic_date = date.today().isoformat()
        else:
            # Validate date format
            try:
                date.fromisoformat(logic_date)
            except ValueError:
                return {
                    "status": "error",
                    "error_message": f"Invalid date format: '{logic_date}'. Expected YYYY-MM-DD",
                    "message": "Please provide date in YYYY-MM-DD format (e.g., '2024-11-24')",
                }

        # Calculate metrics based on table
        if table_name == "customers":
            metrics = _calculate_customers_metrics(logic_date, metric_types)
        elif table_name == "products":
            metrics = _calculate_products_metrics(logic_date, metric_types)
        elif table_name == "sales_transactions":
            metrics = _calculate_sales_transactions_metrics(logic_date, metric_types)
        else:
            return {
                "status": "error",
                "error_message": f"Unsupported table: {table_name}",
                "message": "This table is not yet supported for metric calculation",
            }

        # Check if any metrics were calculated
        if not metrics:
            return {
                "status": "success",
                "table_name": table_name,
                "logic_date": logic_date,
                "metrics_calculated": [],
                "total_metrics": 0,
                "message": f"No data found for {table_name} on {logic_date}",
            }

        # Update the database with calculated metrics
        update_result = _update_quality_metrics_table(table_name, logic_date, metrics)

        if update_result["status"] == "error":
            return update_result

        return {
            "status": "success",
            "table_name": table_name,
            "logic_date": logic_date,
            "metrics_calculated": metrics,
            "total_metrics": len(metrics),
            "message": (
                f"Successfully calculated {len(metrics)} quality metrics "
                f"for {table_name} on {logic_date}"
            ),
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to calculate quality metrics: {str(e)}",
            "message": "An error occurred during quality metric calculation",
        }


def _calculate_customers_metrics(logic_date: str, metric_types: list[str] | None) -> list[dict]:
    """
    Calculate quality metrics for the customers table.

    Metrics calculated:
    - completeness_email: % of customers with non-null email
    - completeness_phone: % of customers with non-null phone
    - completeness_country: % of customers with non-null country
    - consistency_registration_date: % of customers with registration_date <= today
    - uniqueness_customer: % of unique customers (based on name + email)

    Args:
        logic_date: The scope_date to filter data
        metric_types: Optional list of specific metrics to calculate

    Returns:
        List of metric dictionaries with metric_name and metric_value
    """
    with get_db_connection() as conn:
        # Load customers data into Polars DataFrame
        query = f"SELECT * FROM customers WHERE scope_date = '{logic_date}'"
        df = pl.read_database(query, conn)

        if df.is_empty():
            return []

        metrics = []
        total_rows = len(df)

        # Completeness: email
        if metric_types is None or "completeness_email" in metric_types:
            non_null_count = df["email"].drop_nulls().len()
            completeness = float(non_null_count / total_rows)
            metrics.append({"metric_name": "completeness_email", "metric_value": completeness})

        # Completeness: phone
        if metric_types is None or "completeness_phone" in metric_types:
            non_null_count = df["phone"].drop_nulls().len()
            completeness = float(non_null_count / total_rows)
            metrics.append({"metric_name": "completeness_phone", "metric_value": completeness})

        # Completeness: country
        if metric_types is None or "completeness_country" in metric_types:
            non_null_count = df["country"].drop_nulls().len()
            completeness = float(non_null_count / total_rows)
            metrics.append({"metric_name": "completeness_country", "metric_value": completeness})

        # Consistency: registration_date (not in future)
        if metric_types is None or "consistency_registration_date" in metric_types:
            today = date.today()
            valid_count = df.filter(pl.col("registration_date") <= today).height
            consistency = float(valid_count / total_rows)
            metrics.append(
                {"metric_name": "consistency_registration_date", "metric_value": consistency}
            )

        # Uniqueness: customer (based on customer_name + email)
        if metric_types is None or "uniqueness_customer" in metric_types:
            # Count unique combinations of customer_name and email
            unique_count = df.select(["customer_name", "email"]).unique().height
            uniqueness = float(unique_count / total_rows)
            metrics.append({"metric_name": "uniqueness_customer", "metric_value": uniqueness})

        return metrics


def _calculate_products_metrics(logic_date: str, metric_types: list[str] | None) -> list[dict]:
    """
    Calculate quality metrics for the products table.

    Metrics calculated:
    - completeness_product_name: % of products with non-null product_name
    - validity_unit_price: % of products with unit_price >= 0
    - validity_stock_quantity: % of products with stock_quantity >= 0

    Args:
        logic_date: The scope_date to filter data
        metric_types: Optional list of specific metrics to calculate

    Returns:
        List of metric dictionaries with metric_name and metric_value
    """
    with get_db_connection() as conn:
        # Load products data into Polars DataFrame
        query = f"SELECT * FROM products WHERE scope_date = '{logic_date}'"
        df = pl.read_database(query, conn)

        if df.is_empty():
            return []

        metrics = []
        total_rows = len(df)

        # Completeness: product_name
        if metric_types is None or "completeness_product_name" in metric_types:
            non_null_count = df["product_name"].drop_nulls().len()
            completeness = float(non_null_count / total_rows)
            metrics.append(
                {"metric_name": "completeness_product_name", "metric_value": completeness}
            )

        # Validity: unit_price (>= 0)
        if metric_types is None or "validity_unit_price" in metric_types:
            valid_count = df.filter(pl.col("unit_price") >= 0).height
            validity = float(valid_count / total_rows)
            metrics.append({"metric_name": "validity_unit_price", "metric_value": validity})

        # Validity: stock_quantity (>= 0)
        if metric_types is None or "validity_stock_quantity" in metric_types:
            valid_count = df.filter(pl.col("stock_quantity") >= 0).height
            validity = float(valid_count / total_rows)
            metrics.append({"metric_name": "validity_stock_quantity", "metric_value": validity})

        return metrics


def _calculate_sales_transactions_metrics(
    logic_date: str, metric_types: list[str] | None
) -> list[dict]:
    """
    Calculate quality metrics for the sales_transactions table.

    Metrics calculated:
    - completeness_payment_method: % of transactions with non-null payment_method
    - accuracy_total_amount: % of transactions with correct total_amount calculation
    - validity_discount_percent: % of transactions with discount_percent <= 100
    - validity_quantity: % of transactions with quantity > 0
    - integrity_customer_id: % of transactions with valid customer references
    - integrity_product_id: % of transactions with valid product references
    - consistency_transaction_date: % of transactions with transaction_date <= today

    Args:
        logic_date: The scope_date to filter data
        metric_types: Optional list of specific metrics to calculate

    Returns:
        List of metric dictionaries with metric_name and metric_value
    """
    with get_db_connection() as conn:
        # Load sales_transactions data into Polars DataFrame
        query = f"SELECT * FROM sales_transactions WHERE scope_date = '{logic_date}'"
        df = pl.read_database(query, conn)

        if df.is_empty():
            return []

        metrics = []
        total_rows = len(df)

        # Completeness: payment_method
        if metric_types is None or "completeness_payment_method" in metric_types:
            non_null_count = df["payment_method"].drop_nulls().len()
            completeness = float(non_null_count / total_rows)
            metrics.append(
                {"metric_name": "completeness_payment_method", "metric_value": completeness}
            )

        # Accuracy: total_amount (correct calculation)
        if metric_types is None or "accuracy_total_amount" in metric_types:
            # Calculate expected total: quantity * unit_price * (1 - discount_percent / 100)
            df_calc = df.with_columns(
                [
                    (
                        pl.col("quantity").cast(pl.Float64)
                        * pl.col("unit_price").cast(pl.Float64)
                        * (1 - pl.col("discount_percent").cast(pl.Float64) / 100)
                    )
                    .round(2)
                    .alias("expected_total")
                ]
            )
            # Compare with actual total_amount (with tolerance for floating point)
            accurate_count = df_calc.filter(
                (pl.col("total_amount").cast(pl.Float64) - pl.col("expected_total")).abs() < 0.02
            ).height
            accuracy = float(accurate_count / total_rows)
            metrics.append({"metric_name": "accuracy_total_amount", "metric_value": accuracy})

        # Validity: discount_percent (<= 100)
        if metric_types is None or "validity_discount_percent" in metric_types:
            valid_count = df.filter(pl.col("discount_percent") <= 100).height
            validity = float(valid_count / total_rows)
            metrics.append({"metric_name": "validity_discount_percent", "metric_value": validity})

        # Validity: quantity (> 0)
        if metric_types is None or "validity_quantity" in metric_types:
            valid_count = df.filter(pl.col("quantity") > 0).height
            validity = float(valid_count / total_rows)
            metrics.append({"metric_name": "validity_quantity", "metric_value": validity})

        # Integrity: customer_id (customer exists)
        if metric_types is None or "integrity_customer_id" in metric_types:
            # Load customer IDs for the same logic_date
            query_customers = (
                f"SELECT DISTINCT customer_id FROM customers " f"WHERE scope_date = '{logic_date}'"
            )
            customers_df = pl.read_database(query_customers, conn)
            # Semi join to count valid references (only matching records)
            valid_df = df.join(customers_df, on="customer_id", how="inner")
            valid_count = valid_df.height
            integrity = float(valid_count / total_rows)
            metrics.append({"metric_name": "integrity_customer_id", "metric_value": integrity})

        # Integrity: product_id (product exists)
        if metric_types is None or "integrity_product_id" in metric_types:
            # Load product IDs for the same logic_date
            query_products = (
                f"SELECT DISTINCT product_id FROM products " f"WHERE scope_date = '{logic_date}'"
            )
            products_df = pl.read_database(query_products, conn)
            # Semi join to count valid references (only matching records)
            valid_df = df.join(products_df, on="product_id", how="inner")
            valid_count = valid_df.height
            integrity = float(valid_count / total_rows)
            metrics.append({"metric_name": "integrity_product_id", "metric_value": integrity})

        # Consistency: transaction_date (not in future)
        if metric_types is None or "consistency_transaction_date" in metric_types:
            today = date.today()
            valid_count = df.filter(pl.col("transaction_date") <= today).height
            consistency = float(valid_count / total_rows)
            metrics.append(
                {"metric_name": "consistency_transaction_date", "metric_value": consistency}
            )

        return metrics


def _update_quality_metrics_table(table_name: str, logic_date: str, metrics: list[dict]) -> dict:
    """
    Insert or update calculated metrics in the data_quality_metrics table.

    For each metric, checks if a record exists for the same table_name, logic_date,
    and metric_name. If it exists, updates it; otherwise, inserts a new record.

    Args:
        table_name: The table that was analyzed
        logic_date: The scope_date for which metrics were calculated
        metrics: List of metric dictionaries with metric_name and metric_value

    Returns:
        Status dictionary indicating success or error
    """
    try:
        with get_db_connection() as conn:
            calculation_date = datetime.now()

            for metric in metrics:
                metric_name = metric["metric_name"]
                metric_value = Decimal(str(metric["metric_value"]))

                # Check if metric already exists
                existing = conn.execute(
                    """
                    SELECT metric_id FROM data_quality_metrics
                    WHERE table_name = ? AND logic_date = ? AND metric_name = ?
                """,
                    [table_name, logic_date, metric_name],
                ).fetchone()

                if existing:
                    # Update existing metric
                    conn.execute(
                        """
                        UPDATE data_quality_metrics
                        SET metric_value = ?, calculation_date = ?, status = ?
                        WHERE table_name = ? AND logic_date = ? AND metric_name = ?
                    """,
                        [
                            metric_value,
                            calculation_date,
                            "success",
                            table_name,
                            logic_date,
                            metric_name,
                        ],
                    )
                else:
                    # Get next metric_id
                    max_id_result = conn.execute(
                        "SELECT COALESCE(MAX(metric_id), 0) + 1 FROM data_quality_metrics"
                    ).fetchone()
                    next_id = max_id_result[0]

                    # Insert new metric
                    conn.execute(
                        """
                        INSERT INTO data_quality_metrics
                        (metric_id, table_name, metric_name, metric_value, calculation_date,
                         logic_date, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        [
                            next_id,
                            table_name,
                            metric_name,
                            metric_value,
                            calculation_date,
                            logic_date,
                            "success",
                        ],
                    )

            conn.commit()

        return {
            "status": "success",
            "message": f"Successfully updated {len(metrics)} metrics in database",
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to update database: {str(e)}",
            "message": "An error occurred while updating quality metrics table",
        }
