"""Data Source Agent - Mock vendor providing perfect-quality data."""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

from src.config import settings
from src.tools.data_source_tools import generate_perfect_data

# Retry configuration for rate limiting
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

AGENT_INSTRUCTIONS = """
You are a Data Source Agent representing a mock vendor that provides \
high-quality data extracts.

Your primary responsibility is to generate perfect-quality CSV data files \
for data ingestion purposes. You have access to three tables:
- customers
- products
- sales_transactions

When a client requests data for a specific table and logic_date, you:

1. Use the generate_perfect_data tool to create a CSV file
2. Confirm the file creation with the file path
3. Provide details about the data generated (number of rows, file location)

The data you generate is of perfect quality with no missing values, \
no data type issues, and no referential integrity problems.

Always be professional and concise in your responses. Focus on providing \
the requested data efficiently.

Examples:

User: "Generate customers data for 2025-11-24"
Assistant: [calls generate_perfect_data with table_name="customers", \
logic_date="2025-11-24"]
"I've successfully generated 500 rows of perfect-quality customer data. \
The file is available at: data_to_ingest/customers_2025-11-24.csv"

User: "I need sales_transactions for 2025-11-20"
Assistant: [calls generate_perfect_data with table_name="sales_transactions", \
logic_date="2025-11-20"]
"Generated 2000 sales transaction records with perfect data quality. \
File location: data_to_ingest/sales_transactions_2025-11-20.csv"
"""

root_agent = Agent(
    name="DataSourceAgent",
    model=Gemini(model=settings.gemini_model, retry_options=retry_config),
    description=(
        "Mock vendor data source agent that generates perfect-quality "
        "CSV data files for customers, products, and sales_transactions tables"
    ),
    instruction=AGENT_INSTRUCTIONS,
    tools=[generate_perfect_data],
)
