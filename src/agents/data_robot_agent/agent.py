"""Data Robot Agent - Hierarchical leader orchestrator for all data tasks.

The data_robot_agent is the root orchestrator that combines:
1. ParallelAgent: Concurrent capability checking (SQL, Quality, Exploration, Ingestion)
2. SequentialAgent: Request parsing → execution → formatting

Architecture:
    User Request → ParallelAgent (capability checks) → SequentialAgent (routing) → Final Response
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import preload_memory
from google.genai import types

from src.config import settings
from src.agents.data_robot_agent.capability_checker_agents import (
    capability_checker_parallel,
)
from src.agents.data_robot_agent.request_router_agents import request_router_sequential

# ============================================================================
# Retry Configuration
# ============================================================================

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# ============================================================================
# CAPABILITY EXPLANATION FUNCTION
# ============================================================================


def explain_capabilities():
    """Return a comprehensive description of the data_robot_agent's four main capabilities.

    This function provides clear, user-friendly documentation of what the agent can do.

    Returns:
        str: Formatted explanation of all four capabilities with examples.
    """
    explanation = """
# Data Robot Agent - Capabilities Overview

I am the **Data Robot Agent**, your hierarchical orchestrator for all data tasks.
I handle four main capabilities through specialized agents and tools:

---

## 1. 🔍 **Data Exploration** - Explore & Understand Database Structure

### What I Can Do:
- List all available tables in the database with row counts
- Describe table schemas with column types and constraints
- Show business context and purpose of each table
- Display sample data from any table
- Analyze table relationships

### Use Cases:
- "What tables exist in the database?"
- "Describe the customers table"
- "Tell me about the sales_transactions table"
- "Show me the schema for products"
- "What's in the data_quality_metrics table?"

### Under the Hood:
Uses the **Data Exploration Agent** with tools:
- `list_tables()` - Get all tables with row counts
- `describe_table(table_name)` - Show schema and samples
- `get_table_info(table_name)` - Get business context

---

## 2. 💾 **SQL Execution** - Query Data with Natural Language

### What I Can Do:
- Convert natural language questions to SQL queries
- Execute SELECT queries safely
- Filter, sort, aggregate, and join data
- Show results in clear tables or summaries
- Track query history

### Use Cases:
- "Show me the top 5 customers by lifetime value"
- "Count how many sales happened in each region"
- "What's the average order value?"
- "List products with low stock"
- "Show me customer activity in the last month"

### Under the Hood:
Uses the **SQL Agent** with tools:
- Query generator (natural language → SQL)
- `execute_select_query()` - Run SQL safely
- Result formatting and insights

---

## 3. 📊 **Data Quality** - Monitor Data Health & Metrics

### What I Can Do:
- Calculate data quality metrics (completeness, accuracy, consistency, etc.)
- Retrieve historical quality metrics by date or table
- Compare quality trends over time
- Identify data quality issues
- Provide business-friendly quality reports

### Use Cases:
- "What's the quality of the customers table?"
- "Show me quality metrics for 2025-03-01"
- "How complete is the email field?"
- "Are there data quality issues I should know about?"
- "Has data quality improved this month?"

### Under the Hood:
Uses the **Quality Agent** with tools:
- `calculate_quality_metrics(table, date)` - Compute metrics
- `get_quality_metrics_by_table(table)` - Retrieve metrics
- `list_available_scope_dates()` - See available dates
- Trend analysis and business interpretation

---

## 4. 📥 **Data Ingestion** - Load & Validate Data

### What I Can Do:
- Load CSV data into the database
- Validate data against business rules
- Handle data transformations
- Update existing records (upsert)
- Record pipeline execution history

### Use Cases:
- "Load customer data from the CSV file"
- "Ingest the new products file"
- "Validate and load sales transactions"
- "Check ingestion status"
- "Show me the pipeline run history"

### Under the Hood:
Uses the **Ingestion Agent** with tools:
- `load_and_upsert_csv(file, table)` - Load and validate data
- `record_pipeline_run()` - Log ingestion events
- `get_query_history()` - Check activity

---

## 🤖 How I Work

### The Two-Stage Architecture:

**Stage 1: Capability Checking (Parallel)**
When you submit a request, I check all four capabilities in parallel:
- Can I execute SQL? ✓
- Are quality metrics available? ✓
- Can I explore tables? ✓
- Is ingestion ready? ✓

**Stage 2: Request Processing (Sequential)**
Then I process your request through three stages:
1. **Parser**: Analyze your request → determine which capability you need
2. **Executor**: Delegate to the right specialized agent
3. **Formatter**: Present the result in a clear, professional format

---

## 📝 Example Interactions

### Example 1: Data Exploration
**You:** "What tables exist?"
**Me:** [Parallel checks all capabilities, then] "The database contains:
• **customers** - 525 records
• **products** - 150 records
• **sales_transactions** - 5,200 records
..."

### Example 2: SQL Query
**You:** "Show me top 5 customers by spending"
**Me:** [Routes to SQL Agent, executes safe query, formats results]
"Here are your top 5 customers by lifetime value:
| Rank | Customer | Value |
|------|----------|-------|
| 1 | John Doe | $125K |
..."

### Example 3: Data Quality
**You:** "How's the data quality?"
**Me:** [Routes to Quality Agent, retrieves metrics]
"Data quality status:
✅ **Completeness** - 98% excellent
⚠️ **Email Field** - 87% populated (needs attention)
..."

### Example 4: Data Ingestion
**You:** "Load customer data"
**Me:** [Routes to Ingestion Agent, validates and loads]
"Successfully loaded:
✓ 150 new customer records inserted
✓ 45 existing records updated
✓ Pipeline run recorded"

---

## ⚙️ Advanced Features

### State Awareness
I'm aware of system state before routing your request:
- Database connectivity and table availability
- Quality metrics freshness
- Recent pipeline activity
- Query execution history

### Error Recovery
If something goes wrong:
- I explain the issue clearly
- Suggest alternative approaches
- Provide corrected examples
- Keep you informed every step

### Security & Safety
- Only SELECT queries allowed (read-only)
- Data validation before ingestion
- Audit trail of all operations
- No destructive operations

---

## 🚀 Quick Start Commands

Try these to get started:
```
"What tables do we have?"
"Describe customers table"
"Show me top 10 products by price"
"What's the data quality?"
"Load new customer data"
```

---

## 💡 Tips for Best Results

1. **Be specific**: "Show customers from USA" works better than "show data"
2. **Use business language**: I understand your domain concepts
3. **Ask follow-ups**: You can ask about specific aspects of any result
4. **Combine queries**: You can request multiple things in sequence

---

## 📞 Need Help?

Just ask me anything about your data! I'll:
- Route your request to the right capability
- Execute it safely and efficiently
- Explain the results clearly
- Suggest next steps or improvements

---

**I'm ready to help with your data tasks. What would you like to explore?**
"""

    return explanation.strip()


# ============================================================================
# MAIN ROOT AGENT: Data Robot Agent
# ============================================================================
# Orchestrates ParallelAgent for capability checking + SequentialAgent for routing

root_agent = Agent(
    name="data_robot",
    model=Gemini(
        model=settings.gemini_model,
        retry_options=retry_config,
    ),
    description="Hierarchical orchestrator for all data tasks with parallel capability checking and sequential request routing",
    sub_agents=[
        capability_checker_parallel,
        request_router_sequential,
    ],
    instruction="""You are the Data Robot Agent, the root orchestrator for all data tasks.

**Your Two-Stage Architecture:**

**CRITICAL: You MUST complete both stages for every user request!**

1. **Stage 1: Capability Checking (REQUIRED)**
   - ALWAYS start by delegating to capability_checker_parallel
   - This checks all four capabilities in parallel (SQL, Quality, Exploration, Ingestion)
   - Gather capability status from results

2. **Stage 2: Request Processing (REQUIRED)**
   - AFTER checking capabilities, delegate to request_router_sequential  
   - Pass the user request to request_router_sequential
   - It will parse, route to appropriate agent, and format response
   - Return the final response to user

**Your Four Main Capabilities (via delegation):**

1. **SQL Execution** - Execute natural language queries as SQL
   - "Show me top customers", "Count sales by region"
   - Handled by: request_router_sequential → SQL Agent
   
2. **Data Quality** - Analyze data quality metrics and trends
   - "What's the data quality?", "Show metrics for 2025-03-01"
   - Handled by: request_router_sequential → Quality Agent
   
3. **Data Exploration** - Explore database structure and content
   - "What tables exist?", "Describe the customers table"
   - Handled by: request_router_sequential → Exploration Agent
   
4. **Data Ingestion** - Load and validate data
   - "Load customer data from CSV", "Ingest sales transactions"
   - Handled by: request_router_sequential → Ingestion Agent

**Exact Workflow You Must Follow:**

1. User submits request
2. YOU: Delegate to capability_checker_parallel (REQUIRED FIRST STEP)
   ```
   Send request to: CapabilityChecker (the ParallelAgent)
   Get back: JSON with status of all 4 capabilities
   ```
3. YOU: Delegate to request_router_sequential with the user's original request (REQUIRED SECOND STEP)
   ```
   Send request to: RequestRouter (the SequentialAgent)
   Include: Original user request + capability status context
   Get back: Final formatted response
   ```
4. YOU: Present the final response from RequestRouter to user

**Important - DO NOT:**
- Try to process requests yourself
- Skip the capability check stage
- Skip the request routing stage
- Combine them or do them out of order
- Return capability check results as the final answer

**Important - DO:**
- Always run capability_checker_parallel first
- Always run request_router_sequential second (with user's actual request)
- Provide the final formatted response from request_router_sequential to user
- Let the sub_agents handle all the actual work

**Response Format:**
Present the final response from request_router_sequential to the user.
It will be properly formatted markdown with:
- Clear answer to the question
- Business insights and recommendations
- Professional presentation

**Sub-Agents Available:**
- `CapabilityChecker` (ParallelAgent): Checks system state
- `RequestRouter` (SequentialAgent): Processes requests

**Critical Rule:** 
For EVERY user request, you MUST delegate to BOTH sub_agents in order:
1. First: capability_checker_parallel (check what's available)
2. Then: request_router_sequential (process the actual request)

This is how the hierarchical orchestration works. Don't try to skip steps.""",
)

