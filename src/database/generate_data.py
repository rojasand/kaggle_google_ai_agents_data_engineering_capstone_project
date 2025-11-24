"""Generate sample data with intentional quality issues."""

import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from faker import Faker

# Initialize Faker
fake = Faker()
Faker.seed(42)  # For reproducibility
random.seed(42)

# Default scope_date for all generated data
DEFAULT_SCOPE_DATE = date.today()


def generate_customers(num_customers: int = 500) -> list[dict]:
    """
    Generate customer data with intentional quality issues.

    Quality Issues:
    - ~10% missing emails (50 customers)
    - ~5% missing phones (25 customers)
    - ~3% missing countries (15 customers)
    - ~5% duplicates (25 duplicate records)
    - ~2% future registration dates (10 customers)
    - ~2% outliers in lifetime_value (10 customers)

    Args:
        num_customers: Number of customers to generate

    Returns:
        List of customer dictionaries
    """
    customers = []
    customer_segments = ["Premium", "Standard", "Basic", "VIP"]
    countries = ["USA", "Canada", "UK", "Germany", "France", "Australia", "Japan"]

    # Calculate exact counts for quality issues
    missing_email_count = int(num_customers * 0.10)  # 50
    missing_phone_count = int(num_customers * 0.05)  # 25
    missing_country_count = int(num_customers * 0.03)  # 15
    future_date_count = int(num_customers * 0.02)  # 10
    outlier_count = int(num_customers * 0.02)  # 10

    # Create indices for quality issues
    missing_email_indices = set(random.sample(range(num_customers), missing_email_count))
    missing_phone_indices = set(random.sample(range(num_customers), missing_phone_count))
    missing_country_indices = set(random.sample(range(num_customers), missing_country_count))
    future_date_indices = set(random.sample(range(num_customers), future_date_count))
    outlier_indices = set(random.sample(range(num_customers), outlier_count))

    # Generate base customers
    for i in range(num_customers):
        # Normal lifetime value: $100 - $15,000
        if i in outlier_indices:
            # Outliers: $50,000 - $100,000
            lifetime_value = Decimal(str(round(random.uniform(50000, 100000), 2)))
        else:
            lifetime_value = Decimal(str(round(random.uniform(100, 15000), 2)))

        # Registration date
        if i in future_date_indices:
            # Future date: 1-30 days in the future
            reg_date = date.today() + timedelta(days=random.randint(1, 30))
        else:
            # Normal date: 1-3 years ago
            days_ago = random.randint(1, 1095)
            reg_date = date.today() - timedelta(days=days_ago)

        customer = {
            "customer_id": i + 1,
            "customer_name": fake.name(),
            "email": None if i in missing_email_indices else fake.email(),
            "phone": None if i in missing_phone_indices else fake.phone_number(),
            "country": None if i in missing_country_indices else random.choice(countries),
            "registration_date": reg_date,
            "customer_segment": random.choice(customer_segments),
            "lifetime_value": lifetime_value,
            "scope_date": DEFAULT_SCOPE_DATE,
        }
        customers.append(customer)

    # Create duplicates (~5% = 25 duplicates)
    duplicate_count = int(num_customers * 0.05)
    duplicate_source_indices = random.sample(range(num_customers), duplicate_count)

    for source_idx in duplicate_source_indices:
        # Create a duplicate with the same name and email
        original = customers[source_idx]
        duplicate = {
            "customer_id": len(customers) + 1,
            "customer_name": original["customer_name"],
            "email": original["email"],
            "phone": fake.phone_number(),  # Different phone
            "country": random.choice(countries),  # Different country
            "registration_date": original["registration_date"]
            + timedelta(days=random.randint(1, 30)),
            "customer_segment": random.choice(customer_segments),
            "lifetime_value": Decimal(str(round(random.uniform(100, 15000), 2))),
            "scope_date": DEFAULT_SCOPE_DATE,
        }
        customers.append(duplicate)

    return customers


def generate_products(num_products: int = 100) -> list[dict]:
    """
    Generate product data with intentional quality issues.

    Quality Issues:
    - ~8% missing product names (8 products)
    - ~1% negative unit prices (1 product)
    - ~3% outlier unit prices (3 products)
    - ~2% negative stock quantities (2 products)

    Args:
        num_products: Number of products to generate

    Returns:
        List of product dictionaries
    """
    products = []
    categories = {
        "Electronics": ["Laptops", "Smartphones", "Tablets", "Accessories"],
        "Clothing": ["Men", "Women", "Kids", "Shoes"],
        "Home & Garden": ["Furniture", "Kitchen", "Bedding", "Decor"],
        "Sports": ["Fitness", "Outdoor", "Team Sports", "Athletic Wear"],
        "Books": ["Fiction", "Non-Fiction", "Educational", "Children"],
    }

    # Calculate exact counts for quality issues
    missing_name_count = int(num_products * 0.08)  # 8
    negative_price_count = int(num_products * 0.01)  # 1
    outlier_price_count = int(num_products * 0.03)  # 3
    negative_stock_count = int(num_products * 0.02)  # 2

    # Create indices for quality issues
    missing_name_indices = set(random.sample(range(num_products), missing_name_count))
    negative_price_indices = set(random.sample(range(num_products), negative_price_count))
    outlier_price_indices = set(random.sample(range(num_products), outlier_price_count))
    negative_stock_indices = set(random.sample(range(num_products), negative_stock_count))

    for i in range(num_products):
        category = random.choice(list(categories.keys()))
        subcategory = random.choice(categories[category])

        # Unit price
        if i in negative_price_indices:
            # Negative price (error)
            unit_price = Decimal(str(round(random.uniform(-100, -10), 2)))
        elif i in outlier_price_indices:
            # Outlier: $5,000 - $15,000
            unit_price = Decimal(str(round(random.uniform(5000, 15000), 2)))
        else:
            # Normal: $10 - $500
            unit_price = Decimal(str(round(random.uniform(10, 500), 2)))

        # Cost price (70-90% of unit price)
        cost_multiplier = Decimal(str(random.uniform(0.70, 0.90)))
        cost_price = (unit_price * cost_multiplier).quantize(Decimal("0.01"))

        # Stock quantity
        if i in negative_stock_indices:
            # Negative stock (sync error)
            stock_quantity = random.randint(-50, -1)
        else:
            # Normal stock
            stock_quantity = random.randint(0, 1000)

        product = {
            "product_id": i + 1,
            "product_name": None if i in missing_name_indices else fake.catch_phrase(),
            "category": category,
            "subcategory": subcategory,
            "unit_price": unit_price,
            "cost_price": cost_price,
            "supplier_id": random.randint(1, 50),
            "stock_quantity": stock_quantity,
            "reorder_level": random.randint(10, 100),
            "scope_date": DEFAULT_SCOPE_DATE,
        }
        products.append(product)

    return products


def generate_sales_transactions(
    num_transactions: int = 5000,
    num_customers: int = 500,
    num_products: int = 100,
) -> list[dict]:
    """
    Generate sales transaction data with intentional quality issues.

    Quality Issues:
    - ~2% orphaned customer_id (100 transactions)
    - ~2% orphaned product_id (100 transactions)
    - ~1% future transaction dates (50 transactions)
    - ~1% invalid discounts >100% (50 transactions)
    - ~2% calculation errors in total_amount (100 transactions)
    - ~1% negative quantities (50 transactions)
    - ~2% outlier quantities (100 transactions)
    - ~5% missing payment methods (250 transactions)

    Args:
        num_transactions: Number of transactions to generate
        num_customers: Number of customers (for valid IDs)
        num_products: Number of products (for valid IDs)

    Returns:
        List of transaction dictionaries
    """
    transactions = []
    sales_channels = ["Online", "Store", "Mobile", "Phone"]
    regions = ["North", "South", "East", "West", "Central"]
    payment_methods = ["Credit Card", "PayPal", "Bank Transfer", "Cash"]

    # Calculate exact counts for quality issues
    orphaned_customer_count = int(num_transactions * 0.02)  # 100
    orphaned_product_count = int(num_transactions * 0.02)  # 100
    future_date_count = int(num_transactions * 0.01)  # 50
    invalid_discount_count = int(num_transactions * 0.01)  # 50
    calc_error_count = int(num_transactions * 0.02)  # 100
    negative_qty_count = int(num_transactions * 0.01)  # 50
    outlier_qty_count = int(num_transactions * 0.02)  # 100
    missing_payment_count = int(num_transactions * 0.05)  # 250

    # Create indices for quality issues
    orphaned_customer_indices = set(random.sample(range(num_transactions), orphaned_customer_count))
    orphaned_product_indices = set(random.sample(range(num_transactions), orphaned_product_count))
    future_date_indices = set(random.sample(range(num_transactions), future_date_count))
    invalid_discount_indices = set(random.sample(range(num_transactions), invalid_discount_count))
    calc_error_indices = set(random.sample(range(num_transactions), calc_error_count))
    negative_qty_indices = set(random.sample(range(num_transactions), negative_qty_count))
    outlier_qty_indices = set(random.sample(range(num_transactions), outlier_qty_count))
    missing_payment_indices = set(random.sample(range(num_transactions), missing_payment_count))

    for i in range(num_transactions):
        # Customer ID
        if i in orphaned_customer_indices:
            # Orphaned: customer doesn't exist
            customer_id = random.randint(num_customers + 1, num_customers + 500)
        else:
            customer_id = random.randint(1, num_customers)

        # Product ID
        if i in orphaned_product_indices:
            # Orphaned: product doesn't exist
            product_id = random.randint(num_products + 1, num_products + 100)
        else:
            product_id = random.randint(1, num_products)

        # Transaction date
        if i in future_date_indices:
            # Future date: 1-30 days ahead
            trans_date = date.today() + timedelta(days=random.randint(1, 30))
        else:
            # Normal date: past 365 days
            days_ago = random.randint(1, 365)
            trans_date = date.today() - timedelta(days=days_ago)

        # Quantity
        if i in negative_qty_indices:
            # Negative (return not flagged)
            quantity = random.randint(-10, -1)
        elif i in outlier_qty_indices:
            # Outlier: 100-500 items
            quantity = random.randint(100, 500)
        else:
            # Normal: 1-20 items
            quantity = random.randint(1, 20)

        # Unit price (normal range)
        unit_price = Decimal(str(round(random.uniform(10, 500), 2)))

        # Discount
        if i in invalid_discount_indices:
            # Invalid: >100%
            discount_percent = Decimal(str(round(random.uniform(101, 200), 2)))
        else:
            # Normal: 0-50%
            discount_percent = Decimal(str(round(random.uniform(0, 50), 2)))

        # Calculate total amount
        correct_total = (Decimal(quantity) * unit_price * (1 - discount_percent / 100)).quantize(
            Decimal("0.01")
        )

        if i in calc_error_indices:
            # Calculation error: add random error
            error_amount = Decimal(str(round(random.uniform(-100, 100), 2)))
            total_amount = (correct_total + error_amount).quantize(Decimal("0.01"))
        else:
            total_amount = correct_total

        transaction = {
            "transaction_id": i + 1,
            "customer_id": customer_id,
            "product_id": product_id,
            "transaction_date": trans_date,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount_percent": discount_percent,
            "total_amount": total_amount,
            "payment_method": (
                None if i in missing_payment_indices else random.choice(payment_methods)
            ),
            "sales_channel": random.choice(sales_channels),
            "region": random.choice(regions),
            "scope_date": DEFAULT_SCOPE_DATE,
        }
        transactions.append(transaction)

    return transactions


def generate_initial_metrics() -> list[dict]:
    """
    Generate initial data quality metrics.

    Returns:
        List of initial metric dictionaries
    """
    current_time = datetime.now()
    logic_date = date.today()

    metrics = [
        {
            "metric_id": 1,
            "table_name": "customers",
            "metric_name": "completeness_email",
            "metric_value": Decimal("0.90"),  # 90% complete (10% missing)
            "calculation_date": current_time,
            "logic_date": logic_date,
            "status": "success",
        },
        {
            "metric_id": 2,
            "table_name": "sales_transactions",
            "metric_name": "accuracy_total_amount",
            "metric_value": Decimal("0.98"),  # 98% accurate (2% errors)
            "calculation_date": current_time,
            "logic_date": logic_date,
            "status": "success",
        },
    ]

    return metrics


if __name__ == "__main__":
    # Test data generation
    print("Generating test data...")

    customers = generate_customers(500)
    print(f"Generated {len(customers)} customers")
    print(f"  - Missing emails: {sum(1 for c in customers if c['email'] is None)}")
    print(f"  - Missing phones: {sum(1 for c in customers if c['phone'] is None)}")
    print(f"  - Missing countries: {sum(1 for c in customers if c['country'] is None)}")

    products = generate_products(100)
    print(f"\nGenerated {len(products)} products")
    print(f"  - Missing names: {sum(1 for p in products if p['product_name'] is None)}")
    print(f"  - Negative prices: {sum(1 for p in products if p['unit_price'] < 0)}")
    print(f"  - Negative stock: {sum(1 for p in products if p['stock_quantity'] < 0)}")

    transactions = generate_sales_transactions(5000, 500, 100)
    print(f"\nGenerated {len(transactions)} transactions")
    print(f"  - Orphaned customers: {sum(1 for t in transactions if t['customer_id'] > 500)}")
    print(f"  - Orphaned products: {sum(1 for t in transactions if t['product_id'] > 100)}")
    print(f"  - Negative quantities: {sum(1 for t in transactions if t['quantity'] < 0)}")
    print(f"  - Invalid discounts: {sum(1 for t in transactions if t['discount_percent'] > 100)}")
    print(f"  - Missing payment: {sum(1 for t in transactions if t['payment_method'] is None)}")

    metrics = generate_initial_metrics()
    print(f"\nGenerated {len(metrics)} initial metrics")
