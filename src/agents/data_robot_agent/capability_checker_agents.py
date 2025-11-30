"""Parallel capability checkers for concurrent system state assessment.

This module implements four parallel mini-agents that check the availability
and status of the four main data capabilities (SQL, Quality, Exploration, Ingestion).

Architecture:
    - Each checker agent runs concurrently
    - Returns structured JSON with capability status
    - Results aggregated by ParallelAgent for context awareness
"""

from google.adk.agents import Agent, ParallelAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

from src.config import settings
from src.tools import (
    execute_select_query,
    get_query_history,
    list_available_scope_dates,
    get_quality_metrics_by_table,
    list_tables,
    describe_table,
    get_table_info,
)

# ============================================================================
# Retry Configuration (consistent across all agents)
# ============================================================================

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# ============================================================================
# CHECKER 1: SQL Capability Checker
# ============================================================================
# Checks if SQL execution capability is available

sql_checker_agent = Agent(
    name="SQLCapabilityChecker",
    model=Gemini(
        model=settings.gemini_model,
        retry_options=retry_config,
    ),
    tools=[execute_select_query, get_query_history, list_tables],
    instruction="""You are the SQL capability checker. Your job is to quickly verify that SQL query execution is available.

**Your Task:**

1. Call list_tables() to check if database is accessible
2. Return a JSON status object with:
   - capability: "sql"
   - available: true/false (true if list_tables returned success)
   - tables_count: number from list_tables response, or 0 if error
   - status_message: brief explanation (e.g., "SQL execution ready with 3 tables available")
   - last_query_time: optional field from get_query_history if available

**Expected Response Format:**
```json
{
  "capability": "sql",
  "available": true,
  "tables_count": 3,
  "status_message": "SQL execution ready with 3 tables (customers, products, sales_transactions)",
  "last_query_time": "2025-11-29T10:30:00Z"
}
```

**On Error Response:**
```json
{
  "capability": "sql",
  "available": false,
  "tables_count": 0,
  "status_message": "SQL execution unavailable: [error details]",
  "error": true
}
```

IMPORTANT: Output ONLY the JSON object, nothing else.""",
    output_key="sql_capability",
)

# ============================================================================
# CHECKER 2: Data Quality Capability Checker
# ============================================================================
# Checks if quality metrics are available

quality_checker_agent = Agent(
    name="QualityCapabilityChecker",
    model=Gemini(
        model=settings.gemini_model,
        retry_options=retry_config,
    ),
    tools=[list_available_scope_dates, get_quality_metrics_by_table],
    instruction="""You are the quality capability checker. Your job is to verify that data quality metrics are available.

**Your Task:**

1. Call list_available_scope_dates() to check available quality metric dates
2. Extract scope dates from response
3. If dates available, pick the most recent date and call get_quality_metrics_by_table()
   to verify metrics are actually calculated
4. Return a JSON status object with:
   - capability: "quality"
   - available: true/false (true if scope dates exist and metrics retrieved)
   - scope_dates_available: number of available dates
   - latest_scope_date: most recent date with metrics (or null if none)
   - metrics_available: number of metrics for latest date
   - status_message: brief explanation

**Expected Response Format:**
```json
{
  "capability": "quality",
  "available": true,
  "scope_dates_available": 6,
  "latest_scope_date": "2025-03-01",
  "metrics_available": 15,
  "status_message": "Quality metrics available for 6 dates, latest: 2025-03-01 with 15 metrics"
}
```

**On Error Response:**
```json
{
  "capability": "quality",
  "available": false,
  "scope_dates_available": 0,
  "latest_scope_date": null,
  "metrics_available": 0,
  "status_message": "Quality metrics unavailable: [error details]",
  "error": true
}
```

IMPORTANT: Output ONLY the JSON object, nothing else.""",
    output_key="quality_capability",
)

# ============================================================================
# CHECKER 3: Data Exploration Capability Checker
# ============================================================================
# Checks if table exploration is available

exploration_checker_agent = Agent(
    name="ExplorationCapabilityChecker",
    model=Gemini(
        model=settings.gemini_model,
        retry_options=retry_config,
    ),
    tools=[list_tables, describe_table, get_table_info],
    instruction="""You are the exploration capability checker. Your job is to verify that data exploration (table inspection) is available.

**Your Task:**

1. Call list_tables() to get available tables
2. If tables exist, pick the first table and call describe_table() to verify schema inspection works
3. Return a JSON status object with:
   - capability: "exploration"
   - available: true/false (true if tables can be listed and described)
   - tables_available: number of tables
   - first_table_name: name of first table (or null)
   - can_describe: true/false (whether describe_table worked)
   - status_message: brief explanation

**Expected Response Format:**
```json
{
  "capability": "exploration",
  "available": true,
  "tables_available": 3,
  "first_table_name": "customers",
  "can_describe": true,
  "status_message": "Data exploration ready: 3 tables available, schema inspection working"
}
```

**On Error Response:**
```json
{
  "capability": "exploration",
  "available": false,
  "tables_available": 0,
  "first_table_name": null,
  "can_describe": false,
  "status_message": "Data exploration unavailable: [error details]",
  "error": true
}
```

IMPORTANT: Output ONLY the JSON object, nothing else.""",
    output_key="exploration_capability",
)

# ============================================================================
# CHECKER 4: Data Ingestion Capability Checker
# ============================================================================
# Checks if data ingestion is active/available

ingestion_checker_agent = Agent(
    name="IngestionCapabilityChecker",
    model=Gemini(
        model=settings.gemini_model,
        retry_options=retry_config,
    ),
    tools=[list_tables, get_query_history],
    instruction="""You are the ingestion capability checker. Your job is to verify that data ingestion capability is available.

**Your Task:**

1. Call list_tables() to check database connectivity
2. Optionally call get_query_history() to check if pipeline has been active
3. Return a JSON status object with:
   - capability: "ingestion"
   - available: true/false (true if database is accessible for ingestion)
   - tables_count: number of tables (indicates data has been ingested)
   - last_activity: optional timestamp from query history
   - status_message: brief explanation of ingestion status

**Expected Response Format:**
```json
{
  "capability": "ingestion",
  "available": true,
  "tables_count": 3,
  "last_activity": "2025-03-01T15:30:00Z",
  "status_message": "Data ingestion ready: database accessible with 3 tables, last activity 2025-03-01"
}
```

**On Error Response:**
```json
{
  "capability": "ingestion",
  "available": false,
  "tables_count": 0,
  "last_activity": null,
  "status_message": "Data ingestion unavailable: [error details]",
  "error": true
}
```

IMPORTANT: Output ONLY the JSON object, nothing else.""",
    output_key="ingestion_capability",
)

# ============================================================================
# Root Parallel Agent: Concurrent Capability Checking
# ============================================================================

capability_checker_parallel = ParallelAgent(
    name="CapabilityChecker",
    sub_agents=[
        sql_checker_agent,
        quality_checker_agent,
        exploration_checker_agent,
        ingestion_checker_agent,
    ],
)
