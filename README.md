# Data Engineer Assistant Agent

An AI-powered assistant for data engineers to understand, query, and analyze data quality. Built for the [Kaggle 5-Day AI Agents Intensive Course](https://www.kaggle.com/learn-guide/5-day-agents) Capstone Project.

## Overview

This project provides a conversational AI agent that helps data engineers with:
- **Data Quality Analysis**: Identify missing values, duplicates, outliers, and inconsistencies
- **Pipeline Management**: Re-run data pipelines for specific logic dates
- **Data Exploration**: Ask questions about your data and get instant insights
- **Correlation Analysis**: Find relationships between variables
- **Interactive Visualization**: Generate charts and tables on demand

## Tech Stack

- **Database**: DuckDB (fast analytical database)
- **Data Processing**: Polars (high-performance DataFrame library)
- **Agent Framework**: Google Generative AI (Gemini)
- **Chat Interface**: Gradio (web-based UI)
- **Visualization**: Plotly (interactive charts)
- **Logging**: Loguru (simple and powerful logging)

## Project Structure

```
src/
├── config/          # Configuration management
├── database/        # Database connection, models, and data generation
├── agents/          # AI agents (orchestrator, quality, pipeline, analytics)
├── tools/           # Agent tools (profiling, metrics, queries)
├── chat/            # Gradio chat interface
├── memory/          # Session and conversation memory
└── observability/   # Logging and metrics
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/rojasand/kaggle_google_ai_agents_data_engineering_capstone_project.git
cd kaggle_google_ai_agents_data_engineering_capstone_project
```

### 2. Complete Setup (One Command!)

```bash
make setup
```

This will:
- ✅ Install all dependencies with Poetry
- ✅ Create `.env` file from template
- ✅ Initialize database with sample e-commerce data (500 customers, 100 products, 5000 transactions)

### 3. Configure API Key

Edit `.env` and add your Gemini API key:

```bash
# Open .env in your editor
nano .env  # or vim, code, etc.

# Add your key:
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Run the Agent

```bash
make run
```

Open your browser at `http://localhost:7860` to interact with the agent.

## Makefile Commands

All project operations are available through the Makefile:

```bash
make help          # Show all available commands
make install       # Install dependencies only
make setup         # Complete setup (install + database + .env)
make init-db       # Initialize/reinitialize database
make run           # Start the agent (auto-initializes DB if needed)
make launch-jupyter # Start Jupyter Notebook
make test          # Run tests
make test-quality  # Test all 8 data quality indicators
make check-code    # Check code quality (no changes)
make fix-code      # Format and fix code issues
make clean         # Remove virtual environment and caches
make clean-db      # Remove database files
```

## Sample Data

The database contains realistic e-commerce data with **intentional quality issues** for testing data quality tools:

### Tables Overview

#### 1. **customers** (500 rows)
Customer information with various quality issues:

| Column | Type | Description | Quality Issues |
|--------|------|-------------|----------------|
| customer_id | INTEGER | Unique customer identifier | Primary key (clean) |
| customer_name | VARCHAR | Customer full name | ~5% duplicates (same name+email) |
| email | VARCHAR | Email address | ~10% missing values |
| phone | VARCHAR | Phone number | ~5% missing values |
| country | VARCHAR | Customer country | ~3% missing values |
| registration_date | DATE | Account creation date | Some future dates (~2%) |
| customer_segment | VARCHAR | Customer tier (Premium, Standard, Basic, VIP) | Clean |
| lifetime_value | DECIMAL | Total customer spend | ~2% outliers ($50K-$100K vs typical $100-$15K) |

**Example Quality Issues:**
- Missing emails: `NULL` values in email column
- Duplicate customers: Same customer_name + email combination appears multiple times
- Outliers: Some customers with unusually high lifetime_value

#### 2. **products** (100 rows)
Product catalog with pricing and inventory issues:

| Column | Type | Description | Quality Issues |
|--------|------|-------------|----------------|
| product_id | INTEGER | Unique product identifier | Primary key (clean) |
| product_name | VARCHAR | Product name | ~8% missing values |
| category | VARCHAR | Main product category | Clean |
| subcategory | VARCHAR | Product subcategory | Clean |
| unit_price | DECIMAL | Selling price | ~3% outliers ($5K-$15K), ~1% negative |
| cost_price | DECIMAL | Cost of goods | Derived from unit_price |
| supplier_id | INTEGER | Supplier reference | Clean |
| stock_quantity | INTEGER | Current inventory | ~2% negative values (data errors) |
| reorder_level | INTEGER | Reorder threshold | Clean |

**Example Quality Issues:**
- Missing product names: `NULL` in product_name
- Negative prices: unit_price < 0 (data entry errors)
- Negative inventory: stock_quantity < 0 (data sync issues)
- Price outliers: Extremely high prices that may indicate errors

#### 3. **sales_transactions** (5,000 rows)
Sales transactions with calculation errors and referential integrity issues:

| Column | Type | Description | Quality Issues |
|--------|------|-------------|----------------|
| transaction_id | INTEGER | Unique transaction ID | Primary key (clean) |
| customer_id | INTEGER | Customer reference | ~2% orphaned (customer doesn't exist) |
| product_id | INTEGER | Product reference | ~2% orphaned (product doesn't exist) |
| transaction_date | DATE | Transaction date | ~1% future dates |
| quantity | INTEGER | Items purchased | ~2% outliers (100-500), ~1% negative |
| unit_price | DECIMAL | Price at time of sale | Clean |
| discount_percent | DECIMAL | Discount applied | ~1% invalid (>100%) |
| total_amount | DECIMAL | Final transaction amount | ~2% calculation errors |
| payment_method | VARCHAR | Payment type | ~5% missing values |
| sales_channel | VARCHAR | Sales channel (Online, Store, Mobile, Phone) | Clean |
| region | VARCHAR | Sales region | Clean |

**Example Quality Issues:**
- Orphaned references: customer_id or product_id that don't exist in their respective tables
- Future dates: transaction_date > current date
- Invalid discounts: discount_percent > 100
- Calculation errors: total_amount ≠ quantity × unit_price × (1 - discount_percent/100)
- Negative quantities: Returns not properly flagged

#### 4. **data_quality_metrics** (2 rows)
Tracks data quality metrics over time:

| Column | Type | Description |
|--------|------|-------------|
| metric_id | INTEGER | Unique metric ID |
| table_name | VARCHAR | Table being measured |
| metric_name | VARCHAR | Metric type (completeness, accuracy, etc.) |
| metric_value | DECIMAL | Metric score (0-1) |
| calculation_date | TIMESTAMP | When metric was calculated |
| logic_date | DATE | Date for which data is measured |
| status | VARCHAR | Calculation status |

**Initial Metrics:**
- `completeness_email`: 90% (10% missing emails in customers)
- `accuracy_total_amount`: 98% (2% calculation errors in transactions)

#### 5. **pipeline_runs** (0 rows)
Tracks data pipeline execution history:

| Column | Type | Description |
|--------|------|-------------|
| run_id | INTEGER | Unique run ID |
| pipeline_name | VARCHAR | Pipeline identifier |
| logic_date | DATE | Date being processed |
| start_time | TIMESTAMP | Pipeline start time |
| end_time | TIMESTAMP | Pipeline end time |
| status | VARCHAR | Run status (success, failed, running) |
| records_processed | INTEGER | Number of records processed |
| errors_count | INTEGER | Number of errors encountered |
| run_by | VARCHAR | User or system that triggered run |

### Why These Quality Issues?

These intentional data quality problems allow the agent to demonstrate:

1. **Missing Data Detection**: Identify columns with NULL values and calculate completeness metrics
2. **Duplicate Detection**: Find duplicate customer records based on business rules
3. **Outlier Detection**: Identify unusual values in prices, quantities, or customer metrics
4. **Referential Integrity**: Detect orphaned references between tables
5. **Business Rule Validation**: Check for invalid discounts, negative values, future dates
6. **Calculation Accuracy**: Verify computed fields match expected formulas
7. **Data Profiling**: Generate comprehensive data quality reports

## Quality Testing

The project includes comprehensive quality testing to validate all data quality tools and indicators. Run the test suite with:

```bash
make test-quality
```

This command tests **8 categories of quality indicators**:

### 1. **Data Profiling**
Generates comprehensive statistics for tables and columns:
- Row counts and column counts
- Missing value percentages
- Distinct value counts
- Numeric statistics (min, max, mean, stddev)
- Data types and sample values

**Example Output:**
```
Table: customers
  Rows: 500
  Columns: 8
  Column 'email': 460 non-null (92.0%), 242 distinct values
  Column 'lifetime_value': min=124.56, max=99847.23, mean=8998.36
```

### 2. **Completeness Checks**
Calculates missing data rates:
- Percentage of non-null values per column
- Count of missing values
- Completeness score (0-100%)

**Example Output:**
```
Completeness for 'customers.email':
  Completeness: 92.0%
  Non-null: 460
  Null: 40
```

### 3. **Duplicate Detection**
Finds duplicate records based on business keys:
- Groups duplicates by specified columns
- Counts occurrences of each duplicate
- Returns all duplicate groups

**Example Output:**
```
Duplicates found: 26 groups, 49 duplicate rows
Example: "John Smith" with email "john@example.com" appears 3 times
```

### 4. **Validity Checks**
Validates business rules:
- Negative prices (unit_price < 0)
- Missing product names
- Invalid discounts (discount_percent > 100)
- Negative quantities
- Missing payment methods

**Example Output:**
```
Validity Issues:
  negative_price: 1 rows (1.00%)
  missing_name: 9 rows (9.00%)
  invalid_discount: 64 rows (1.28%)
  negative_quantity: 49 rows (0.98%)
  missing_payment: 254 rows (5.08%)
```

### 5. **Referential Integrity**
Detects orphaned foreign key references:
- Checks customer_id references in transactions
- Checks product_id references in transactions
- Identifies records pointing to non-existent parent records

**Example Output:**
```
Referential Integrity Issues:
  customer_id: 659 orphaned records (13.19%)
  product_id: 1428 orphaned records (28.57%)
```

### 6. **Outlier Detection**
Identifies statistical anomalies using two methods:
- **IQR Method**: Values beyond Q1 - 1.5×IQR or Q3 + 1.5×IQR
- **Z-Score Method**: Values with |z| > 3 (3 standard deviations)

**Example Output:**
```
Outliers in 'customers.lifetime_value' (IQR method):
  Found: 11 outliers
  Bounds: lower=-7342.51, upper=22339.25
  Examples: 50234.12, 75893.45, 99847.23

Outliers in 'products.unit_price' (Z-score method):
  Found: 6 outliers
  Examples: 5234.56, 8792.34
```

### 7. **Correlation Analysis**
Calculates relationships between numeric columns:
- Pearson correlation coefficient
- Identifies strongly correlated variables
- Useful for feature selection and redundancy detection

**Example Output:**
```
Correlation: unit_price vs cost_price = 0.9996
(Strong positive correlation - cost is derived from price)
```

### 8. **Value Distribution**
Analyzes frequency of categorical values:
- Counts occurrences of each unique value
- Orders by frequency (descending)
- Identifies most common categories

**Example Output:**
```
Distribution of 'payment_method':
  PayPal: 1010 transactions (21.4%)
  Bank Transfer: 967 transactions (20.5%)
  Credit Card: 942 transactions (20.0%)
  (other): 1827 transactions (38.1%)
```

### Test Results Summary

When you run `make test-quality`, you'll see output for all 8 categories demonstrating that:
- ✅ All quality tools are working correctly
- ✅ Intentional data issues are properly detected
- ✅ Statistics match expected patterns (e.g., ~8% missing emails, ~5% duplicates)
- ✅ All quality indicators can be used by the AI agent

The test validates the foundation that the AI agent will use to answer questions like:
- "How many customers have missing emails?"
- "Show me all duplicate customers"
- "Find outliers in transaction amounts"
- "What's the data quality score for the products table?"
- "Check referential integrity between sales and customers"

## Features

### Data Quality Analysis
- Completeness checks (missing values)
- Uniqueness validation (duplicates)
- Accuracy verification (calculation errors)
- Consistency checks (referential integrity)
- Outlier detection (statistical anomalies)

### Pipeline Management
- Re-run pipelines for specific dates
- Track pipeline execution history
- Monitor data quality metrics over time

### Interactive Queries
- Natural language queries about your data
- SQL generation from user questions
- Results displayed as tables or charts

### Visualization
- Automatic chart generation
- Distribution plots
- Time series analysis
- Correlation matrices

## Example Queries

Ask the agent questions like:
- "How many customers have missing email addresses?"
- "Show me products with negative prices"
- "What's the average transaction amount by region?"
- "Find duplicate customers"
- "Calculate the completeness metric for all tables"
- "Show me transactions with calculation errors"
- "What are the top 10 customers by lifetime value?"
- "Re-run the sales pipeline for 2025-11-15"

## Development

### Running Tests
```bash
make test
```

### Code Quality
```bash
make check-code    # Check code without making changes
make fix-code      # Auto-fix formatting and linting issues
```

### Resetting the Database
```bash
make clean-db      # Remove database files
make init-db       # Recreate with fresh sample data
```

### Full Cleanup
```bash
make clean         # Remove virtual environment and all caches
make setup         # Start fresh with complete setup
```

## License

MIT License - see LICENSE file for details.

## Troubleshooting

### Database Issues
If you encounter database errors:
```bash
make clean-db    # Remove corrupted database
make init-db     # Recreate fresh database
```

### Dependency Issues
If dependencies are out of sync:
```bash
make clean       # Remove everything
make setup       # Fresh installation
```

### API Key Not Working
1. Verify your `.env` file has the correct key: `GEMINI_API_KEY=your_key_here`
2. Ensure no extra spaces or quotes around the key
3. Restart the agent: `make run`

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Run `make check-code` before committing
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built as part of the [Kaggle 5-Day AI Agents Intensive Course](https://www.kaggle.com/learn-guide/5-day-agents) with Google (Nov 10-14, 2025).
