"""Tools for ingestion_agent to load and upsert CSV data into database."""

from datetime import datetime
from pathlib import Path

import polars as pl
from pydantic import ValidationError

from src.database.connection import get_db_connection
from src.database.models import Customer, Product, SalesTransaction


def load_and_upsert_csv(file_path: str, table_name: str) -> dict:
    """
    Load a CSV file, validate its schema, and upsert data into database.

    This tool performs the following steps:
    1. Validates the file exists
    2. Reads the CSV using Polars
    3. Validates each row against the Pydantic model
    4. Upserts data into the database table
    5. Records pipeline run metadata

    Args:
        file_path: Path to the CSV file to load
        table_name: Target database table name
                   Valid options: 'customers', 'products', 'sales_transactions'

    Returns:
        dict: Status dictionary with ingestion results

    Example:
        >>> load_and_upsert_csv("data_to_ingest/customers_2025-11-24.csv", "customers")
        {
            "status": "success",
            "table_name": "customers",
            "rows_processed": 500,
            "rows_inserted": 100,
            "rows_updated": 400,
            "validation_errors": 0,
            "message": "Successfully ingested 500 rows into customers"
        }
    """
    try:
        # Validate table name
        valid_tables = ["customers", "products", "sales_transactions"]
        if table_name not in valid_tables:
            return {
                "status": "error",
                "error_message": (
                    f"Invalid table name. Valid options: {', '.join(valid_tables)}"
                ),
                "message": "Failed to load data",
            }

        # Validate file exists
        csv_path = Path(file_path)
        if not csv_path.exists():
            return {
                "status": "error",
                "error_message": f"File not found: {file_path}",
                "message": "Failed to load data",
            }

        # Read CSV
        try:
            df = pl.read_csv(file_path)
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Failed to read CSV: {str(e)}",
                "message": "Failed to load data",
            }

        if df.is_empty():
            return {
                "status": "error",
                "error_message": "CSV file is empty",
                "message": "Failed to load data",
            }

        # Validate schema and upsert based on table
        if table_name == "customers":
            result = _upsert_customers(df)
        elif table_name == "products":
            result = _upsert_products(df)
        else:  # sales_transactions
            result = _upsert_sales_transactions(df)

        return result

    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": "An unexpected error occurred during data ingestion",
        }


def _upsert_customers(df: pl.DataFrame) -> dict:
    """Validate and upsert customer data."""
    validation_errors = []
    rows_inserted = 0
    rows_updated = 0

    with get_db_connection() as conn:
        for row_dict in df.to_dicts():
            # Validate with Pydantic model
            try:
                Customer(**row_dict)
            except ValidationError as e:
                validation_errors.append({
                    "customer_id": row_dict.get("customer_id"),
                    "errors": str(e),
                })
                continue

            # Check if record exists
            existing = conn.execute(
                "SELECT customer_id FROM customers WHERE customer_id = ?",
                [row_dict["customer_id"]],
            ).fetchone()

            if existing:
                # Update existing record
                conn.execute(
                    """
                    UPDATE customers SET
                        customer_name = ?,
                        email = ?,
                        phone = ?,
                        country = ?,
                        registration_date = ?,
                        customer_segment = ?,
                        lifetime_value = ?,
                        scope_date = ?
                    WHERE customer_id = ?
                    """,
                    [
                        row_dict["customer_name"],
                        row_dict["email"],
                        row_dict["phone"],
                        row_dict["country"],
                        row_dict["registration_date"],
                        row_dict["customer_segment"],
                        row_dict["lifetime_value"],
                        row_dict["scope_date"],
                        row_dict["customer_id"],
                    ],
                )
                rows_updated += 1
            else:
                # Insert new record
                conn.execute(
                    """
                    INSERT INTO customers (
                        customer_id, customer_name, email, phone,
                        country, registration_date, customer_segment,
                        lifetime_value, scope_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        row_dict["customer_id"],
                        row_dict["customer_name"],
                        row_dict["email"],
                        row_dict["phone"],
                        row_dict["country"],
                        row_dict["registration_date"],
                        row_dict["customer_segment"],
                        row_dict["lifetime_value"],
                        row_dict["scope_date"],
                    ],
                )
                rows_inserted += 1

        conn.commit()

    total_rows = len(df)
    successful_rows = rows_inserted + rows_updated

    if validation_errors:
        return {
            "status": "partial_success",
            "table_name": "customers",
            "rows_processed": total_rows,
            "rows_inserted": rows_inserted,
            "rows_updated": rows_updated,
            "validation_errors": len(validation_errors),
            "error_details": validation_errors[:5],  # First 5 errors
            "message": (
                f"Ingested {successful_rows}/{total_rows} rows into customers. "
                f"{len(validation_errors)} rows failed validation."
            ),
        }

    return {
        "status": "success",
        "table_name": "customers",
        "rows_processed": total_rows,
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "validation_errors": 0,
        "message": f"Successfully ingested {successful_rows} rows into customers",
    }


def _upsert_products(df: pl.DataFrame) -> dict:
    """Validate and upsert product data."""
    validation_errors = []
    rows_inserted = 0
    rows_updated = 0

    with get_db_connection() as conn:
        for row_dict in df.to_dicts():
            # Validate with Pydantic model
            try:
                Product(**row_dict)
            except ValidationError as e:
                validation_errors.append({
                    "product_id": row_dict.get("product_id"),
                    "errors": str(e),
                })
                continue

            # Check if record exists
            existing = conn.execute(
                "SELECT product_id FROM products WHERE product_id = ?",
                [row_dict["product_id"]],
            ).fetchone()

            if existing:
                # Update existing record
                conn.execute(
                    """
                    UPDATE products SET
                        product_name = ?,
                        category = ?,
                        subcategory = ?,
                        unit_price = ?,
                        cost_price = ?,
                        supplier_id = ?,
                        stock_quantity = ?,
                        reorder_level = ?,
                        scope_date = ?
                    WHERE product_id = ?
                    """,
                    [
                        row_dict["product_name"],
                        row_dict["category"],
                        row_dict["subcategory"],
                        row_dict["unit_price"],
                        row_dict["cost_price"],
                        row_dict["supplier_id"],
                        row_dict["stock_quantity"],
                        row_dict["reorder_level"],
                        row_dict["scope_date"],
                        row_dict["product_id"],
                    ],
                )
                rows_updated += 1
            else:
                # Insert new record
                conn.execute(
                    """
                    INSERT INTO products (
                        product_id, product_name, category, subcategory,
                        unit_price, cost_price, supplier_id,
                        stock_quantity, reorder_level, scope_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        row_dict["product_id"],
                        row_dict["product_name"],
                        row_dict["category"],
                        row_dict["subcategory"],
                        row_dict["unit_price"],
                        row_dict["cost_price"],
                        row_dict["supplier_id"],
                        row_dict["stock_quantity"],
                        row_dict["reorder_level"],
                        row_dict["scope_date"],
                    ],
                )
                rows_inserted += 1

        conn.commit()

    total_rows = len(df)
    successful_rows = rows_inserted + rows_updated

    if validation_errors:
        return {
            "status": "partial_success",
            "table_name": "products",
            "rows_processed": total_rows,
            "rows_inserted": rows_inserted,
            "rows_updated": rows_updated,
            "validation_errors": len(validation_errors),
            "error_details": validation_errors[:5],
            "message": (
                f"Ingested {successful_rows}/{total_rows} rows into products. "
                f"{len(validation_errors)} rows failed validation."
            ),
        }

    return {
        "status": "success",
        "table_name": "products",
        "rows_processed": total_rows,
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "validation_errors": 0,
        "message": f"Successfully ingested {successful_rows} rows into products",
    }


def _upsert_sales_transactions(df: pl.DataFrame) -> dict:
    """Validate and upsert sales transaction data."""
    validation_errors = []
    rows_inserted = 0
    rows_updated = 0

    with get_db_connection() as conn:
        for row_dict in df.to_dicts():
            # Validate with Pydantic model
            try:
                SalesTransaction(**row_dict)
            except ValidationError as e:
                validation_errors.append({
                    "transaction_id": row_dict.get("transaction_id"),
                    "errors": str(e),
                })
                continue

            # Check if record exists
            existing = conn.execute(
                "SELECT transaction_id FROM sales_transactions WHERE transaction_id = ?",
                [row_dict["transaction_id"]],
            ).fetchone()

            if existing:
                # Update existing record
                conn.execute(
                    """
                    UPDATE sales_transactions SET
                        customer_id = ?,
                        product_id = ?,
                        transaction_date = ?,
                        quantity = ?,
                        unit_price = ?,
                        discount_percent = ?,
                        total_amount = ?,
                        payment_method = ?,
                        sales_channel = ?,
                        region = ?,
                        scope_date = ?
                    WHERE transaction_id = ?
                    """,
                    [
                        row_dict["customer_id"],
                        row_dict["product_id"],
                        row_dict["transaction_date"],
                        row_dict["quantity"],
                        row_dict["unit_price"],
                        row_dict["discount_percent"],
                        row_dict["total_amount"],
                        row_dict["payment_method"],
                        row_dict["sales_channel"],
                        row_dict["region"],
                        row_dict["scope_date"],
                        row_dict["transaction_id"],
                    ],
                )
                rows_updated += 1
            else:
                # Insert new record
                conn.execute(
                    """
                    INSERT INTO sales_transactions (
                        transaction_id, customer_id, product_id,
                        transaction_date, quantity, unit_price,
                        discount_percent, total_amount, payment_method,
                        sales_channel, region, scope_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        row_dict["transaction_id"],
                        row_dict["customer_id"],
                        row_dict["product_id"],
                        row_dict["transaction_date"],
                        row_dict["quantity"],
                        row_dict["unit_price"],
                        row_dict["discount_percent"],
                        row_dict["total_amount"],
                        row_dict["payment_method"],
                        row_dict["sales_channel"],
                        row_dict["region"],
                        row_dict["scope_date"],
                    ],
                )
                rows_inserted += 1

        conn.commit()

    total_rows = len(df)
    successful_rows = rows_inserted + rows_updated

    if validation_errors:
        return {
            "status": "partial_success",
            "table_name": "sales_transactions",
            "rows_processed": total_rows,
            "rows_inserted": rows_inserted,
            "rows_updated": rows_updated,
            "validation_errors": len(validation_errors),
            "error_details": validation_errors[:5],
            "message": (
                f"Ingested {successful_rows}/{total_rows} rows into sales_transactions. "
                f"{len(validation_errors)} rows failed validation."
            ),
        }

    return {
        "status": "success",
        "table_name": "sales_transactions",
        "rows_processed": total_rows,
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "validation_errors": 0,
        "message": f"Successfully ingested {successful_rows} rows into sales_transactions",
    }


def record_pipeline_run(
    pipeline_name: str, logic_date: str, status: str, records_processed: int, errors_count: int
) -> dict:
    """
    Record a pipeline run in the pipeline_runs table.

    Args:
        pipeline_name: Name of the pipeline
        logic_date: Date being processed (YYYY-MM-DD)
        status: Run status (success, failed, running)
        records_processed: Number of records processed
        errors_count: Number of errors encountered

    Returns:
        dict: Status dictionary with run_id
    """
    try:
        with get_db_connection() as conn:
            # Get next run_id
            next_id = conn.execute(
                "SELECT COALESCE(MAX(run_id), 0) + 1 FROM pipeline_runs"
            ).fetchone()[0]

            # Insert pipeline run
            conn.execute(
                """
                INSERT INTO pipeline_runs (
                    run_id, pipeline_name, logic_date, start_time,
                    end_time, status, records_processed, errors_count, run_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    next_id,
                    pipeline_name,
                    logic_date,
                    datetime.now(),
                    datetime.now(),
                    status,
                    records_processed,
                    errors_count,
                    "ingestion_agent",
                ],
            )
            conn.commit()

            return {
                "status": "success",
                "run_id": next_id,
                "message": f"Recorded pipeline run with ID {next_id}",
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": "Failed to record pipeline run",
        }
