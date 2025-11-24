"""Initialize the DuckDB database with tables and sample data."""

import sys

from loguru import logger

from src.config import settings
from src.database.connection import get_db_connection
from src.database.generate_data import (
    generate_customers,
    generate_initial_metrics,
    generate_products,
    generate_sales_transactions,
)


def create_tables(conn) -> None:
    """Create all database tables."""
    logger.info("Creating database tables...")

    # Drop existing tables if they exist
    conn.execute("DROP TABLE IF EXISTS pipeline_runs")
    conn.execute("DROP TABLE IF EXISTS data_quality_metrics")
    conn.execute("DROP TABLE IF EXISTS sales_transactions")
    conn.execute("DROP TABLE IF EXISTS products")
    conn.execute("DROP TABLE IF EXISTS customers")

    # Create customers table
    conn.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            customer_name VARCHAR NOT NULL,
            email VARCHAR,
            phone VARCHAR,
            country VARCHAR,
            registration_date DATE NOT NULL,
            customer_segment VARCHAR NOT NULL,
            lifetime_value DECIMAL(10, 2) NOT NULL,
            scope_date DATE NOT NULL
        )
    """)
    logger.info("  ✓ Created customers table")

    # Create products table
    conn.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name VARCHAR,
            category VARCHAR NOT NULL,
            subcategory VARCHAR NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            cost_price DECIMAL(10, 2) NOT NULL,
            supplier_id INTEGER NOT NULL,
            stock_quantity INTEGER NOT NULL,
            reorder_level INTEGER NOT NULL,
            scope_date DATE NOT NULL
        )
    """)
    logger.info("  ✓ Created products table")

    # Create sales_transactions table
    conn.execute("""
        CREATE TABLE sales_transactions (
            transaction_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            transaction_date DATE NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            discount_percent DECIMAL(5, 2) NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            payment_method VARCHAR,
            sales_channel VARCHAR NOT NULL,
            region VARCHAR NOT NULL,
            scope_date DATE NOT NULL
        )
    """)
    logger.info("  ✓ Created sales_transactions table")

    # Create data_quality_metrics table
    conn.execute("""
        CREATE TABLE data_quality_metrics (
            metric_id INTEGER PRIMARY KEY,
            table_name VARCHAR NOT NULL,
            metric_name VARCHAR NOT NULL,
            metric_value DECIMAL(5, 4) NOT NULL,
            calculation_date TIMESTAMP NOT NULL,
            logic_date DATE NOT NULL,
            status VARCHAR NOT NULL
        )
    """)
    logger.info("  ✓ Created data_quality_metrics table")

    # Create pipeline_runs table
    conn.execute("""
        CREATE TABLE pipeline_runs (
            run_id INTEGER PRIMARY KEY,
            pipeline_name VARCHAR NOT NULL,
            logic_date DATE NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            status VARCHAR NOT NULL,
            records_processed INTEGER NOT NULL,
            errors_count INTEGER NOT NULL,
            run_by VARCHAR NOT NULL
        )
    """)
    logger.info("  ✓ Created pipeline_runs table")


def insert_customers(conn, customers: list[dict]) -> None:
    """Insert customer data."""
    logger.info(f"Inserting {len(customers)} customers...")

    for customer in customers:
        conn.execute(
            """
            INSERT INTO customers (
                customer_id, customer_name, email, phone, country,
                registration_date, customer_segment, lifetime_value, scope_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                customer["customer_id"],
                customer["customer_name"],
                customer["email"],
                customer["phone"],
                customer["country"],
                customer["registration_date"],
                customer["customer_segment"],
                customer["lifetime_value"],
                customer["scope_date"],
            ],
        )

    logger.info(f"  ✓ Inserted {len(customers)} customers")


def insert_products(conn, products: list[dict]) -> None:
    """Insert product data."""
    logger.info(f"Inserting {len(products)} products...")

    for product in products:
        conn.execute(
            """
            INSERT INTO products (
                product_id, product_name, category, subcategory, unit_price,
                cost_price, supplier_id, stock_quantity, reorder_level, scope_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                product["product_id"],
                product["product_name"],
                product["category"],
                product["subcategory"],
                product["unit_price"],
                product["cost_price"],
                product["supplier_id"],
                product["stock_quantity"],
                product["reorder_level"],
                product["scope_date"],
            ],
        )

    logger.info(f"  ✓ Inserted {len(products)} products")


def insert_transactions(conn, transactions: list[dict]) -> None:
    """Insert sales transaction data."""
    logger.info(f"Inserting {len(transactions)} transactions...")

    for transaction in transactions:
        conn.execute(
            """
            INSERT INTO sales_transactions (
                transaction_id, customer_id, product_id, transaction_date,
                quantity, unit_price, discount_percent, total_amount,
                payment_method, sales_channel, region, scope_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                transaction["transaction_id"],
                transaction["customer_id"],
                transaction["product_id"],
                transaction["transaction_date"],
                transaction["quantity"],
                transaction["unit_price"],
                transaction["discount_percent"],
                transaction["total_amount"],
                transaction["payment_method"],
                transaction["sales_channel"],
                transaction["region"],
                transaction["scope_date"],
            ],
        )

    logger.info(f"  ✓ Inserted {len(transactions)} transactions")


def insert_metrics(conn, metrics: list[dict]) -> None:
    """Insert initial quality metrics."""
    logger.info(f"Inserting {len(metrics)} initial metrics...")

    for metric in metrics:
        conn.execute(
            """
            INSERT INTO data_quality_metrics (
                metric_id, table_name, metric_name, metric_value,
                calculation_date, logic_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            [
                metric["metric_id"],
                metric["table_name"],
                metric["metric_name"],
                metric["metric_value"],
                metric["calculation_date"],
                metric["logic_date"],
                metric["status"],
            ],
        )

    logger.info(f"  ✓ Inserted {len(metrics)} metrics")


def verify_data(conn) -> None:
    """Verify the inserted data."""
    logger.info("Verifying data...")

    # Count rows in each table
    tables = [
        "customers",
        "products",
        "sales_transactions",
        "data_quality_metrics",
        "pipeline_runs",
    ]

    for table in tables:
        result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        count = result[0]
        logger.info(f"  ✓ {table}: {count} rows")

    # Verify quality issues
    logger.info("\nVerifying intentional quality issues:")

    # Missing emails
    missing_emails = conn.execute(
        "SELECT COUNT(*) FROM customers WHERE email IS NULL"
    ).fetchone()[0]
    logger.info(f"  ✓ Missing emails: {missing_emails} (~10% of 525 = 52.5)")

    # Missing phones
    missing_phones = conn.execute(
        "SELECT COUNT(*) FROM customers WHERE phone IS NULL"
    ).fetchone()[0]
    logger.info(f"  ✓ Missing phones: {missing_phones} (~5% of 525 = 26.25)")

    # Missing product names
    missing_names = conn.execute(
        "SELECT COUNT(*) FROM products WHERE product_name IS NULL"
    ).fetchone()[0]
    logger.info(f"  ✓ Missing product names: {missing_names} (~8% of 100 = 8)")

    # Negative prices
    negative_prices = conn.execute(
        "SELECT COUNT(*) FROM products WHERE unit_price < 0"
    ).fetchone()[0]
    logger.info(f"  ✓ Negative prices: {negative_prices} (~1% of 100 = 1)")

    # Orphaned customers
    orphaned_customers = conn.execute(
        """
        SELECT COUNT(*) FROM sales_transactions
        WHERE customer_id NOT IN (SELECT customer_id FROM customers)
    """
    ).fetchone()[0]
    logger.info(f"  ✓ Orphaned customers: {orphaned_customers} (~2% of 5000 = 100)")

    # Orphaned products
    orphaned_products = conn.execute(
        """
        SELECT COUNT(*) FROM sales_transactions
        WHERE product_id NOT IN (SELECT product_id FROM products)
    """
    ).fetchone()[0]
    logger.info(f"  ✓ Orphaned products: {orphaned_products} (~2% of 5000 = 100)")

    # Invalid discounts
    invalid_discounts = conn.execute(
        "SELECT COUNT(*) FROM sales_transactions WHERE discount_percent > 100"
    ).fetchone()[0]
    logger.info(f"  ✓ Invalid discounts: {invalid_discounts} (~1% of 5000 = 50)")

    # Missing payment methods
    missing_payments = conn.execute(
        "SELECT COUNT(*) FROM sales_transactions WHERE payment_method IS NULL"
    ).fetchone()[0]
    logger.info(f"  ✓ Missing payment methods: {missing_payments} (~5% of 5000 = 250)")


def initialize_database() -> None:
    """Initialize the database with tables and sample data."""
    logger.info("=" * 70)
    logger.info("INITIALIZING DATA ENGINEER DATABASE")
    logger.info("=" * 70)

    # Ensure directories exist
    settings.ensure_directories()

    # Check if database already exists
    if settings.database_file.exists():
        logger.warning(f"Database already exists at: {settings.database_file}")
        logger.warning("It will be recreated with fresh data.")

    try:
        with get_db_connection() as conn:
            # Create tables
            create_tables(conn)

            # Generate data
            logger.info("\nGenerating sample data with quality issues...")
            customers = generate_customers(500)
            products = generate_products(100)
            transactions = generate_sales_transactions(5000, 500, 100)
            metrics = generate_initial_metrics()

            # Insert data
            logger.info("\nInserting data into database...")
            insert_customers(conn, customers)
            insert_products(conn, products)
            insert_transactions(conn, transactions)
            insert_metrics(conn, metrics)

            # Verify data
            logger.info("\n" + "=" * 70)
            verify_data(conn)

        logger.info("\n" + "=" * 70)
        logger.info("✓ DATABASE INITIALIZATION COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"Database location: {settings.database_file}")
        logger.info(f"Database size: {settings.database_file.stat().st_size / 1024:.2f} KB")
        logger.info("")

    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        raise


def main():
    """Main entry point."""
    # Configure logger
    logger.remove()
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | <level>{message}</level>"
        ),
        level="INFO",
    )

    try:
        initialize_database()
        return 0
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
