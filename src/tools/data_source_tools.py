"""Tools for data_source_agent to generate perfect-quality CSV data."""

from datetime import date, datetime
from pathlib import Path

import polars as pl
from faker import Faker

fake = Faker()
Faker.seed(42)  # For reproducibility


def generate_perfect_data(table_name: str, logic_date: str) -> dict:
    """
    Generate perfect-quality CSV data for a given table and logic date.

    This tool creates a CSV file with synthetic data that has no quality issues.
    The data matches the schema of the specified table and is ready for ingestion.

    Args:
        table_name: Name of the table to generate data for.
                   Valid options: 'customers', 'products', 'sales_transactions'
        logic_date: Date for which to generate data (format: YYYY-MM-DD)

    Returns:
        dict: Status dictionary with file path and metadata

    Example:
        >>> generate_perfect_data("customers", "2025-11-24")
        {
            "status": "success",
            "file_path": "data_to_ingest/customers_2025-11-24.csv",
            "table_name": "customers",
            "logic_date": "2025-11-24",
            "rows_generated": 500,
            "message": "Successfully generated 500 rows of perfect data"
        }
    """
    try:
        # Validate table name
        valid_tables = ["customers", "products", "sales_transactions"]
        if table_name not in valid_tables:
            return {
                "status": "error",
                "error_message": f"Invalid table name. Valid options: {', '.join(valid_tables)}",
                "message": "Failed to generate data",
            }

        # Parse and validate logic_date
        try:
            parsed_date = datetime.strptime(logic_date, "%Y-%m-%d").date()
        except ValueError:
            return {
                "status": "error",
                "error_message": "Invalid date format. Expected YYYY-MM-DD",
                "message": "Failed to generate data",
            }

        # Generate data based on table
        if table_name == "customers":
            df = _generate_perfect_customers(parsed_date, num_rows=500)
        elif table_name == "products":
            df = _generate_perfect_products(parsed_date, num_rows=200)
        else:  # sales_transactions
            df = _generate_perfect_sales_transactions(parsed_date, num_rows=2000)

        # Create output directory if it doesn't exist
        output_dir = Path("data_to_ingest")
        output_dir.mkdir(exist_ok=True)

        # Generate file path
        file_path = output_dir / f"{table_name}_{logic_date}.csv"

        # Write CSV
        df.write_csv(file_path)

        return {
            "status": "success",
            "file_path": str(file_path),
            "table_name": table_name,
            "logic_date": logic_date,
            "rows_generated": len(df),
            "message": f"Successfully generated {len(df)} rows of perfect data for {table_name}",
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": "An unexpected error occurred while generating data",
        }


def _generate_perfect_customers(scope_date: date, num_rows: int = 500) -> pl.DataFrame:
    """Generate perfect-quality customer data."""
    data = []
    segments = ["Premium", "Standard", "Basic", "VIP"]

    for i in range(1, num_rows + 1):
        # All fields populated (no nulls)
        customer = {
            "customer_id": i,
            "customer_name": fake.name(),
            "email": fake.email(),  # Always present
            "phone": fake.phone_number(),  # Always present
            "country": fake.country(),  # Always present
            "registration_date": fake.date_between(
                start_date="-2y", end_date=scope_date
            ).isoformat(),
            "customer_segment": fake.random_element(segments),
            "lifetime_value": str(round(fake.random.uniform(100, 50000), 2)),
            "scope_date": scope_date.isoformat(),
        }
        data.append(customer)

    return pl.DataFrame(data)


def _generate_perfect_products(scope_date: date, num_rows: int = 200) -> pl.DataFrame:
    """Generate perfect-quality product data."""
    data = []
    categories = {
        "Electronics": ["Laptops", "Phones", "Tablets", "Accessories"],
        "Clothing": ["Men", "Women", "Kids", "Accessories"],
        "Home & Garden": ["Furniture", "Decor", "Kitchen", "Outdoor"],
        "Sports": ["Fitness", "Outdoor", "Team Sports", "Water Sports"],
        "Books": ["Fiction", "Non-Fiction", "Educational", "Comics"],
    }

    for i in range(1, num_rows + 1):
        category = fake.random_element(list(categories.keys()))
        subcategory = fake.random_element(categories[category])

        # Ensure positive prices and cost < unit_price
        cost = round(fake.random.uniform(10, 200), 2)
        unit_price = round(cost * fake.random.uniform(1.2, 3.0), 2)

        product = {
            "product_id": i,
            "product_name": fake.catch_phrase(),  # Always present
            "category": category,
            "subcategory": subcategory,
            "unit_price": str(unit_price),
            "cost_price": str(cost),
            "supplier_id": fake.random_int(min=1, max=50),
            "stock_quantity": fake.random_int(min=10, max=1000),  # Always positive
            "reorder_level": fake.random_int(min=5, max=100),
            "scope_date": scope_date.isoformat(),
        }
        data.append(product)

    return pl.DataFrame(data)


def _generate_perfect_sales_transactions(scope_date: date, num_rows: int = 2000) -> pl.DataFrame:
    """Generate perfect-quality sales transaction data."""
    data = []
    payment_methods = ["Credit Card", "Debit Card", "Cash", "PayPal", "Bank Transfer"]
    sales_channels = ["Online", "Store", "Mobile", "Phone"]
    regions = ["North", "South", "East", "West", "Central"]

    # Ensure valid customer_ids and product_ids
    customer_ids = list(range(1, 501))  # Matches customer count
    product_ids = list(range(1, 201))  # Matches product count

    for i in range(1, num_rows + 1):
        quantity = fake.random_int(min=1, max=10)
        unit_price = round(fake.random.uniform(10, 500), 2)
        discount_percent = round(fake.random.uniform(0, 20), 2)  # Max 20%

        # Calculate total_amount correctly
        subtotal = unit_price * quantity
        discount_amount = subtotal * (discount_percent / 100)
        total_amount = round(subtotal - discount_amount, 2)

        transaction = {
            "transaction_id": i,
            "customer_id": fake.random_element(customer_ids),
            "product_id": fake.random_element(product_ids),
            "transaction_date": fake.date_between(
                start_date="-1y",
                end_date=scope_date,  # Never future dates
            ).isoformat(),
            "quantity": quantity,
            "unit_price": str(unit_price),
            "discount_percent": str(discount_percent),
            "total_amount": str(total_amount),
            "payment_method": fake.random_element(payment_methods),  # Always present
            "sales_channel": fake.random_element(sales_channels),
            "region": fake.random_element(regions),
            "scope_date": scope_date.isoformat(),
        }
        data.append(transaction)

    return pl.DataFrame(data)
