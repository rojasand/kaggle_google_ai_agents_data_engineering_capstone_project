"""SQL Query Agent - Natural language to SQL query execution.

This agent converts natural language questions into SQL queries,
executes them safely, and presents the results in a user-friendly format.

Architecture:
    - Query Generator: Converts natural language to SELECT SQL
    - Query Executor: Executes query and saves to history
    - Results Formatter: Presents results with insights
"""

from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

from src.config import settings
from src.tools.query_tools import execute_select_query

# Configure retry logic
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Agent 1: Query Generator
# Converts natural language to SQL SELECT queries
query_generator_agent = Agent(
    name="QueryGenerator",
    model=Gemini(
        model=settings.gemini_model,
        retry_options=retry_config,
    ),
    instruction="""You are a SQL query generator specialized in converting natural language
questions into valid SELECT SQL queries for a DuckDB database.

DATABASE SCHEMA:
- customers: customer_id, customer_name, email, phone, country, registration_date,
             customer_segment, lifetime_value, scope_date
- products: product_id, product_name, category, subcategory, unit_price,
           cost_price, supplier_id, stock_quantity, reorder_level, scope_date
- sales_transactions: transaction_id, customer_id, product_id, transaction_date,
                     quantity, unit_price, discount_percent, total_amount,
                     payment_method, sales_channel, region, scope_date
- data_quality_metrics: metric_id, table_name, metric_name, metric_value,
                       calculation_date, logic_date, status

YOUR TASK:
1. Analyze the user's natural language question
2. Generate a valid SELECT SQL query that answers the question
3. Return ONLY the SQL query as plain text (no markdown, no code blocks)
4. Ensure the query is syntactically correct for DuckDB
5. Use appropriate JOINs, aggregations, and filters

GUIDELINES:
- Only generate SELECT queries (read-only)
- Use proper table and column names from the schema
- Include appropriate WHERE clauses for filtering
- Use GROUP BY for aggregations
- Use ORDER BY and LIMIT when relevant
- Format dates as YYYY-MM-DD in WHERE clauses
- Use meaningful column aliases for readability

SAFETY:
- NEVER generate DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, or TRUNCATE
- Queries will be validated before execution

EXAMPLES:
User: "How many customers do we have?"
Response: SELECT COUNT(*) as total_customers FROM customers

User: "Show me the top 5 products by price"
Response: SELECT product_name, unit_price FROM products ORDER BY unit_price DESC LIMIT 5

User: "What's the average order value by region?"
Response: SELECT region, AVG(total_amount) as avg_order_value FROM sales_transactions
GROUP BY region ORDER BY avg_order_value DESC

Return ONLY the SQL query text, nothing else.""",
    output_key="generated_sql",
)

# Agent 2: Query Executor
# Executes the generated SQL and tracks in history
query_executor_agent = Agent(
    name="QueryExecutor",
    model=Gemini(
        model=settings.gemini_model,
        retry_options=retry_config,
    ),
    tools=[execute_select_query],
    instruction="""You execute SQL queries safely using the execute_select_query tool.

INPUT:
- You receive a SQL query from the previous agent in 'generated_sql'

YOUR TASK:
1. Take the SQL query from 'generated_sql'
2. Call execute_select_query(query_text=<sql>, session_id=<optional>)
3. Return the complete execution result

TOOL USAGE:
- The tool will validate the query for safety
- It will execute the query if valid
- It will save execution to query_history table
- It returns results with status, rows_returned, results, columns

OUTPUT FORMAT:
Return the complete tool response as JSON. Do not modify or format the response.

Example:
{
    "status": "success",
    "query_text": "SELECT COUNT(*) FROM customers",
    "session_id": "abc-123",
    "rows_returned": 1,
    "results": [{"count": 525}],
    "columns": ["count"],
    "message": "Query executed successfully, returned 1 rows"
}""",
    output_key="execution_result",
)

# Agent 3: Results Formatter
# Formats execution results for user-friendly presentation
results_formatter_agent = Agent(
    name="ResultsFormatter",
    model=Gemini(
        model=settings.gemini_model,
        retry_options=retry_config,
    ),
    instruction="""You present SQL query results in a clear, user-friendly format.

INPUT:
- 'generated_sql': The SQL query that was executed
- 'execution_result': The query execution result (status, results, etc.)

YOUR TASK:
Present the results in this exact format:

**SQL Query:**
```sql
<the SQL query>
```

**Results:**
<format results as a markdown table if multiple rows, or as key-value if single row>

**Summary:**
<provide a 1-2 sentence insight about the results>

FORMATTING GUIDELINES:

For SINGLE ROW results (e.g., COUNT, SUM, AVG):
- Present as bullet points with clear labels
- Example: "• Total Customers: 525"

For MULTIPLE ROWS results:
- Present as markdown table with headers
- Limit to first 20 rows if more (indicate "... X more rows")
- Align numbers right, text left

For EMPTY results:
- State clearly: "No results found."
- Suggest why (e.g., filters too restrictive)

For ERRORS:
- Show error message clearly
- Suggest what might be wrong
- Offer to help reformulate the query

EXAMPLES:

Example 1 (Single aggregation):
**SQL Query:**
```sql
SELECT COUNT(*) as total FROM customers
```

**Results:**
• Total Customers: 525

**Summary:**
The database contains 525 customer records.

Example 2 (Multiple rows):
**SQL Query:**
```sql
SELECT region, COUNT(*) as customer_count FROM customers GROUP BY region LIMIT 5
```

**Results:**
| Region      | Customer Count |
|-------------|----------------|
| North       | 132            |
| South       | 125            |
| East        | 118            |
| West        | 110            |
| Central     | 40             |

**Summary:**
Customer distribution across regions shows North has the highest count with 132 customers.

Example 3 (Error):
**SQL Query:**
```sql
SELECT * FROM unknown_table
```

**Results:**
❌ Query execution failed: Table 'unknown_table' does not exist.

**Summary:**
The table name might be incorrect. Available tables include: customers, products,
sales_transactions, data_quality_metrics.

Always maintain this structure and be helpful in your summaries.""",
)

# Root agent: Sequential pipeline
# Chains the three agents: Generator → Executor → Formatter
root_agent = SequentialAgent(
    name="SQLAgent",
    sub_agents=[
        query_generator_agent,  # 1. Convert natural language to SQL
        query_executor_agent,  # 2. Execute SQL safely
        results_formatter_agent,  # 3. Format results for user
    ],
)
