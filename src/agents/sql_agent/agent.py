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

ROW LIMITING (IMPORTANT):
- For queries that retrieve individual records (SELECT * FROM table), automatically
  add "LIMIT 20" UNLESS the user explicitly requests "all", "complete", "entire",
  "every", or "full" data
- Do NOT add LIMIT for aggregation queries (queries with COUNT, SUM, AVG, MAX, MIN,
  or GROUP BY) - these already return summarized results
- Do NOT add LIMIT if user specifies a different limit (e.g., "top 5", "first 100")
- Do NOT add LIMIT if the query already has a LIMIT clause

EXAMPLES OF AUTOMATIC LIMITING:
User: "show me customer data" → Add LIMIT 20
User: "list products" → Add LIMIT 20
User: "display sales transactions" → Add LIMIT 20

EXAMPLES OF NO LIMITING:
User: "show me ALL customer data" → No LIMIT (user said "all")
User: "count customers by region" → No LIMIT (aggregation with GROUP BY)
User: "what's the average order value" → No LIMIT (aggregation with AVG)
User: "show me top 5 products" → Use LIMIT 5 (user specified)

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

User: "Show me customer data"
Response: SELECT * FROM customers LIMIT 20

User: "List all products"
Response: SELECT * FROM products LIMIT 20

User: "Display ALL customer records"
Response: SELECT * FROM customers

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
<if results were limited, add a note: "Showing first N rows of M total (limited for performance)">

**Summary:**
<provide a 1-2 sentence insight about the results>

FORMATTING GUIDELINES:

For SINGLE ROW results (e.g., COUNT, SUM, AVG):
- Present as bullet points with clear labels
- Example: "• Total Customers: 525"

For MULTIPLE ROWS results:
- Present as markdown table with headers
- Show ALL returned rows (they're already limited by the query)
- If execution_result contains 'is_limited': true, add a note after the table:
  "📊 Showing first N rows (limited for performance).
  Ask for 'all data' to see complete results."
  where N is the actual rows_returned value from execution_result
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

Example 3 (Limited results):
**SQL Query:**
```sql
SELECT * FROM customers LIMIT 20
```

**Results:**
| Customer ID | Customer Name | Email              | Country |
|-------------|---------------|--------------------|---------|
| 1           | John Doe      | john@example.com   | USA     |
| 2           | Jane Smith    | jane@example.com   | Canada  |
...(18 more rows)

📊 Showing first 20 rows (limited for performance). Ask for 'all data' to see complete results.

**Summary:**
Displaying sample of customer records. Database contains more customers.

Example 4 (Error):
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
