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

# Date range for data generation
DATA_START_DATE = date(2025, 1, 1)
DATA_END_DATE = date(2025, 3, 1)
CUSTOMER_REG_START = date(2024, 1, 1)  # Customers can register up to 1 year before


def generate_customers(num_customers: int = 500, scope_date: date = None) -> list[dict]:
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
        scope_date: Date when this data is ingested (defaults to today)

    Returns:
        List of customer dictionaries
    """
    if scope_date is None:
        scope_date = DEFAULT_SCOPE_DATE
    
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

        # Registration date: between CUSTOMER_REG_START and scope_date (or slightly after for quality issues)
        if i in future_date_indices:
            # Future date: 1-30 days after scope_date (quality issue)
            reg_date = scope_date + timedelta(days=random.randint(1, 30))
        else:
            # Normal date: between CUSTOMER_REG_START and scope_date
            days_range = (scope_date - CUSTOMER_REG_START).days
            if days_range > 0:
                days_ago = random.randint(1, days_range)
                reg_date = scope_date - timedelta(days=days_ago)
            else:
                reg_date = CUSTOMER_REG_START

        customer = {
            "customer_id": i + 1,
            "customer_name": fake.name(),
            "email": None if i in missing_email_indices else fake.email(),
            "phone": None if i in missing_phone_indices else fake.phone_number(),
            "country": None if i in missing_country_indices else random.choice(countries),
            "registration_date": reg_date,
            "customer_segment": random.choice(customer_segments),
            "lifetime_value": lifetime_value,
            "scope_date": scope_date,
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
            "scope_date": scope_date,
        }
        customers.append(duplicate)

    return customers


def generate_products(num_products: int = 100, scope_date: date = None) -> list[dict]:
    """
    Generate product data with intentional quality issues.

    Quality Issues:
    - ~8% missing product names (8 products)
    - ~1% negative unit prices (1 product)
    - ~3% outlier unit prices (3 products)
    - ~2% negative stock quantities (2 products)

    Args:
        num_products: Number of products to generate
        scope_date: Date when this data is ingested (defaults to today)

    Returns:
        List of product dictionaries
    """
    if scope_date is None:
        scope_date = DEFAULT_SCOPE_DATE
    
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
            "scope_date": scope_date,
        }
        products.append(product)

    return products


def generate_sales_transactions(
    num_transactions: int = 5000,
    customers: list[dict] = None,
    products: list[dict] = None,
    scope_date: date = None,
) -> list[dict]:
    """
    Generate sales transaction data with intentional quality issues.
    Now uses actual customer and product data for referential integrity.

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
        customers: List of customer dictionaries (for referential integrity)
        products: List of product dictionaries (for referential integrity)
        scope_date: Date when this data is ingested (defaults to today)

    Returns:
        List of transaction dictionaries
    """
    if scope_date is None:
        scope_date = DEFAULT_SCOPE_DATE
    
    # Backward compatibility: if old parameters passed, create dummy data
    if customers is None:
        customers = [{"customer_id": i+1, "registration_date": CUSTOMER_REG_START} for i in range(500)]
    if products is None:
        products = [{"product_id": i+1, "unit_price": Decimal(str(random.uniform(10, 500)))} for i in range(100)]
    
    num_customers = len(customers)
    num_products = len(products)
    
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
        # Customer ID and selection
        if i in orphaned_customer_indices:
            # Orphaned: customer doesn't exist
            customer_id = random.randint(num_customers + 1, num_customers + 500)
            customer_reg_date = CUSTOMER_REG_START  # Fallback
        else:
            # Select valid customer
            customer = random.choice(customers)
            customer_id = customer["customer_id"]
            customer_reg_date = customer["registration_date"]

        # Product ID and selection
        if i in orphaned_product_indices:
            # Orphaned: product doesn't exist
            product_id = random.randint(num_products + 1, num_products + 100)
            # Use random price for orphaned products
            product_unit_price = Decimal(str(round(random.uniform(10, 500), 2)))
        else:
            # Select valid product
            product = random.choice(products)
            product_id = product["product_id"]
            product_unit_price = product["unit_price"]

        # Transaction date: must be >= customer registration date and <= DATA_END_DATE
        if i in future_date_indices:
            # Future date: 1-30 days after scope_date (quality issue)
            trans_date = scope_date + timedelta(days=random.randint(1, 30))
        else:
            # Normal date: between customer registration and DATA_END_DATE
            # Use max of customer_reg_date and DATA_START_DATE as start
            start_date = max(customer_reg_date, DATA_START_DATE)
            if start_date < DATA_END_DATE:
                days_range = (DATA_END_DATE - start_date).days
                if days_range > 0:
                    days_offset = random.randint(0, days_range)
                    trans_date = start_date + timedelta(days=days_offset)
                else:
                    trans_date = start_date
            else:
                trans_date = DATA_END_DATE

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

        # Unit price: use actual product price (with small variation for realism)
        if i not in orphaned_product_indices:
            # Use product price with 0-10% variation
            price_variation = Decimal(str(random.uniform(0.95, 1.05)))
            unit_price = (product_unit_price * price_variation).quantize(Decimal("0.01"))
        else:
            # Random price for orphaned products
            unit_price = product_unit_price

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
            "scope_date": scope_date,
        }
        transactions.append(transaction)

    return transactions


def generate_initial_metrics(logic_date: date = None) -> list[dict]:
    """
    Generate initial data quality metrics.

    Args:
        logic_date: Date for which metrics are calculated (defaults to today)

    Returns:
        List of initial metric dictionaries
    """
    if logic_date is None:
        logic_date = date.today()
    
    current_time = datetime.now()

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


def generate_all_data_with_timeline() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """
    Generate all data with a two-phase timeline:
    1. Faulty data batch (scope_date = 2025-01-01)
    2. Corrected data batch (scope_date = 2025-02-01)
    
    This creates a realistic scenario where initial data has quality issues,
    and a later batch has corrections applied.
    
    Returns:
        Tuple of (all_customers, all_products, all_transactions, all_metrics)
    """
    all_customers = []
    all_products = []
    all_transactions = []
    all_metrics = []
    
    # Phase 1: Generate FAULTY data (2025-01-01)
    faulty_scope_date = date(2025, 1, 1)
    logger_msg = "Generating Phase 1: FAULTY data (scope_date=2025-01-01)"
    print(f"\n{'='*70}")
    print(logger_msg)
    print(f"{'='*70}")
    
    faulty_customers = generate_customers(num_customers=500, scope_date=faulty_scope_date)
    faulty_products = generate_products(num_products=100, scope_date=faulty_scope_date)
    faulty_transactions = generate_sales_transactions(
        num_transactions=5000,
        customers=faulty_customers,
        products=faulty_products,
        scope_date=faulty_scope_date
    )
    faulty_metrics = generate_initial_metrics(logic_date=faulty_scope_date)
    
    all_customers.extend(faulty_customers)
    all_products.extend(faulty_products)
    all_transactions.extend(faulty_transactions)
    all_metrics.extend(faulty_metrics)
    
    print(f"Phase 1 complete: {len(faulty_customers)} customers, {len(faulty_products)} products, {len(faulty_transactions)} transactions")
    
    # Phase 2: Generate CORRECTED data (2025-02-01)
    corrected_scope_date = date(2025, 2, 1)
    logger_msg = "Generating Phase 2: CORRECTED data (scope_date=2025-02-01)"
    print(f"\n{'='*70}")
    print(logger_msg)
    print(f"{'='*70}")
    
    # Temporarily modify random seed to generate corrected data
    original_seed_state = random.getstate()
    random.seed(100)  # Different seed for corrected data
    fake.seed_instance(100)
    
    # Generate corrected customers (start with ID offset to avoid duplicates)
    corrected_customers = []
    customer_id_offset = len(all_customers)
    
    # Generate fewer quality issues for corrected batch
    num_corrected_customers = 500
    for i in range(num_corrected_customers):
        customer = {
            "customer_id": customer_id_offset + i + 1,
            "customer_name": fake.name(),
            "email": fake.email(),  # Always present (fixed)
            "phone": fake.phone_number(),  # Always present (fixed)
            "country": random.choice(["USA", "Canada", "UK", "Germany", "France", "Australia", "Japan"]),
            "registration_date": corrected_scope_date - timedelta(days=random.randint(1, 30)),
            "customer_segment": random.choice(["Premium", "Standard", "Basic", "VIP"]),
            "lifetime_value": Decimal(str(round(random.uniform(100, 15000), 2))),
            "scope_date": corrected_scope_date,
        }
        corrected_customers.append(customer)
    
    # Generate corrected products (start with ID offset)
    corrected_products = []
    product_id_offset = len(all_products)
    num_corrected_products = 100
    
    categories = {
        "Electronics": ["Laptops", "Smartphones", "Tablets", "Accessories"],
        "Clothing": ["Men", "Women", "Kids", "Shoes"],
        "Home & Garden": ["Furniture", "Kitchen", "Bedding", "Decor"],
        "Sports": ["Fitness", "Outdoor", "Team Sports", "Athletic Wear"],
        "Books": ["Fiction", "Non-Fiction", "Educational", "Children"],
    }
    
    for i in range(num_corrected_products):
        category = random.choice(list(categories.keys()))
        subcategory = random.choice(categories[category])
        unit_price = Decimal(str(round(random.uniform(10, 500), 2)))
        cost_price = (unit_price * Decimal(str(random.uniform(0.70, 0.90)))).quantize(Decimal("0.01"))
        
        product = {
            "product_id": product_id_offset + i + 1,
            "product_name": fake.catch_phrase(),  # Always present (fixed)
            "category": category,
            "subcategory": subcategory,
            "unit_price": unit_price,
            "cost_price": cost_price,
            "supplier_id": random.randint(1, 50),
            "stock_quantity": random.randint(0, 1000),  # Always positive (fixed)
            "reorder_level": random.randint(10, 100),
            "scope_date": corrected_scope_date,
        }
        corrected_products.append(product)
    
    # Generate corrected transactions (no orphaned records)
    # Use ALL customers and products (both faulty and corrected batches)
    all_available_customers = all_customers + corrected_customers
    all_available_products = all_products + corrected_products
    
    corrected_transactions = []
    transaction_id_offset = len(all_transactions)
    num_corrected_transactions = 5000
    
    for i in range(num_corrected_transactions):
        # Always use valid customers and products (no orphans)
        customer = random.choice(all_available_customers)
        product = random.choice(all_available_products)
        
        customer_id = customer["customer_id"]
        product_id = product["product_id"]
        customer_reg_date = customer["registration_date"]
        
        # Transaction date: between customer registration and DATA_END_DATE
        start_date = max(customer_reg_date, corrected_scope_date)
        if start_date < DATA_END_DATE:
            days_range = (DATA_END_DATE - start_date).days
            if days_range > 0:
                trans_date = start_date + timedelta(days=random.randint(0, days_range))
            else:
                trans_date = start_date
        else:
            trans_date = DATA_END_DATE
        
        # Normal quantities (no negatives, fewer outliers)
        quantity = random.randint(1, 20)
        
        # Use actual product price
        unit_price = (product["unit_price"] * Decimal(str(random.uniform(0.95, 1.05)))).quantize(Decimal("0.01"))
        
        # Normal discount (0-50%)
        discount_percent = Decimal(str(round(random.uniform(0, 50), 2)))
        
        # Correct calculation
        total_amount = (Decimal(quantity) * unit_price * (1 - discount_percent / 100)).quantize(Decimal("0.01"))
        
        transaction = {
            "transaction_id": transaction_id_offset + i + 1,
            "customer_id": customer_id,
            "product_id": product_id,
            "transaction_date": trans_date,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount_percent": discount_percent,
            "total_amount": total_amount,
            "payment_method": random.choice(["Credit Card", "PayPal", "Bank Transfer", "Cash"]),
            "sales_channel": random.choice(["Online", "Store", "Mobile", "Phone"]),
            "region": random.choice(["North", "South", "East", "West", "Central"]),
            "scope_date": corrected_scope_date,
        }
        corrected_transactions.append(transaction)
    
    # Restore original random state
    random.setstate(original_seed_state)
    
    all_customers.extend(corrected_customers)
    all_products.extend(corrected_products)
    all_transactions.extend(corrected_transactions)
    
    # Generate metrics for corrected batch
    corrected_metrics = [
        {
            "metric_id": len(all_metrics) + 1,
            "table_name": "customers",
            "metric_name": "completeness_email",
            "metric_value": Decimal("1.00"),  # 100% complete
            "calculation_date": datetime.now(),
            "logic_date": corrected_scope_date,
            "status": "success",
        },
        {
            "metric_id": len(all_metrics) + 2,
            "table_name": "sales_transactions",
            "metric_name": "accuracy_total_amount",
            "metric_value": Decimal("1.00"),  # 100% accurate
            "calculation_date": datetime.now(),
            "logic_date": corrected_scope_date,
            "status": "success",
        },
    ]
    all_metrics.extend(corrected_metrics)
    
    print(f"Phase 2 complete: {len(corrected_customers)} customers, {len(corrected_products)} products, {len(corrected_transactions)} transactions")
    print(f"\nTotal: {len(all_customers)} customers, {len(all_products)} products, {len(all_transactions)} transactions, {len(all_metrics)} metrics")
    
    return all_customers, all_products, all_transactions, all_metrics


if __name__ == "__main__":
    # Test data generation with timeline
    print("\n" + "="*70)
    print("TESTING TWO-PHASE DATA GENERATION")
    print("="*70)
    
    customers, products, transactions, metrics = generate_all_data_with_timeline()
    
    print(f"\n" + "="*70)
    print("QUALITY ANALYSIS")
    print("="*70)
    
    # Analyze Phase 1 (faulty) data
    phase1_customers = [c for c in customers if c['scope_date'] == date(2025, 1, 1)]
    phase1_products = [p for p in products if p['scope_date'] == date(2025, 1, 1)]
    phase1_transactions = [t for t in transactions if t['scope_date'] == date(2025, 1, 1)]
    
    print(f"\nPhase 1 (2025-01-01) - FAULTY DATA:")
    print(f"  Customers: {len(phase1_customers)}")
    print(f"    - Missing emails: {sum(1 for c in phase1_customers if c['email'] is None)}")
    print(f"    - Missing phones: {sum(1 for c in phase1_customers if c['phone'] is None)}")
    print(f"  Products: {len(phase1_products)}")
    print(f"    - Missing names: {sum(1 for p in phase1_products if p['product_name'] is None)}")
    print(f"    - Negative prices: {sum(1 for p in phase1_products if p['unit_price'] < 0)}")
    print(f"  Transactions: {len(phase1_transactions)}")
    print(f"    - Negative quantities: {sum(1 for t in phase1_transactions if t['quantity'] < 0)}")
    print(f"    - Invalid discounts: {sum(1 for t in phase1_transactions if t['discount_percent'] > 100)}")
    
    # Analyze Phase 2 (corrected) data
    phase2_customers = [c for c in customers if c['scope_date'] == date(2025, 2, 1)]
    phase2_products = [p for p in products if p['scope_date'] == date(2025, 2, 1)]
    phase2_transactions = [t for t in transactions if t['scope_date'] == date(2025, 2, 1)]
    
    print(f"\nPhase 2 (2025-02-01) - CORRECTED DATA:")
    print(f"  Customers: {len(phase2_customers)}")
    print(f"    - Missing emails: {sum(1 for c in phase2_customers if c['email'] is None)}")
    print(f"    - Missing phones: {sum(1 for c in phase2_customers if c['phone'] is None)}")
    print(f"  Products: {len(phase2_products)}")
    print(f"    - Missing names: {sum(1 for p in phase2_products if p['product_name'] is None)}")
    print(f"    - Negative prices: {sum(1 for p in phase2_products if p['unit_price'] < 0)}")
    print(f"  Transactions: {len(phase2_transactions)}")
    print(f"    - Negative quantities: {sum(1 for t in phase2_transactions if t['quantity'] < 0)}")
    print(f"    - Invalid discounts: {sum(1 for t in phase2_transactions if t['discount_percent'] > 100)}")
    
    print(f"\n" + "="*70)
    print(f"TOTAL: {len(customers)} customers, {len(products)} products, {len(transactions)} transactions")
    print("="*70)
