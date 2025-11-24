"""Multi-agent data exploration system with tool selection, execution, and narration.

This module implements a sequential workflow with three specialized agents:
1. Tool Selector Agent - Analyzes user prompts and decides which tool to use
2. Tool Executor Agent - Executes the selected tool and returns JSON response
3. Narrative Agent - Converts JSON into human-readable text

Architecture:
    User Prompt → Selector Agent → Executor Agent → Narrative Agent → Human-Readable Response
"""

from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

from src.config import settings
from src.tools import (
    describe_table,
    get_quality_metrics_by_scope_date,
    get_quality_metrics_by_table,
    get_table_info,
    list_available_scope_dates,
    list_tables,
)

# Configure retry logic for rate limiting
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# ============================================================================
# AGENT 1: Tool Selector Agent
# ============================================================================
# This agent analyzes the user's request and decides which tool to use

tool_selector_agent = Agent(
    name="ToolSelectorAgent",
    model=Gemini(
        model=settings.gemini_model,
        retry_options=retry_config,
    ),
    instruction="""You are a tool selection specialist. Your job is to analyze the user's request
and decide which database exploration tool to use, OR explain your capabilities if the request
is outside your scope.

**Available Tools:**

**Database Exploration:**
1. list_tables - Use when user asks: "what tables exist", "show tables",
   "list all tables", "what data do you have"
2. describe_table - Use when user asks about a SPECIFIC table's structure:
   "describe customers table", "show schema for products"
3. get_table_info - Use when user asks for complete info about a table:
   "tell me about customers", "explain the sales_transactions table"

**Quality Metrics:**
4. list_available_scope_dates - Use when user asks: "what dates have metrics",
   "when was data ingested", "available scope dates"
5. get_quality_metrics_by_scope_date - Use when user asks about quality for a date:
   "quality metrics for 2024-11-24", "show quality on Nov 24"
6. get_quality_metrics_by_table - Use when user asks about table quality:
   "quality of customers table", "customers quality metrics"

**Your Response Format:**

If the request matches one of your tools, respond with ONLY a JSON object:

```json
{
  "tool_name": "list_tables|describe_table|get_table_info|list_available_scope_dates|get_quality_metrics_by_scope_date|get_quality_metrics_by_table",
  "parameters": {
    "table_name": "table_name_if_needed",
    "scope_date": "YYYY-MM-DD_if_needed"
  },
  "reasoning": "brief explanation of why this tool was chosen"
}
```

If the request is OUTSIDE your capabilities (e.g., data analysis, queries, modifications),
respond with this format:

```json
{
  "tool_name": "out_of_scope",
  "parameters": {},
  "reasoning": "Request is outside available capabilities"
}
```

**Examples:**

User: "What tables are available?"
Response:
```json
{
  "tool_name": "list_tables",
  "parameters": {},
  "reasoning": "User wants to see all available tables"
}
```

User: "Describe the customers table"
Response:
```json
{
  "tool_name": "describe_table",
  "parameters": {"table_name": "customers"},
  "reasoning": "User wants the schema structure of the customers table"
}
```

User: "Tell me about the products table"
Response:
```json
{
  "tool_name": "get_table_info",
  "parameters": {"table_name": "products"},
  "reasoning": "User wants complete information including business context"
}
```

User: "What dates have quality metrics?"
Response:
```json
{
  "tool_name": "list_available_scope_dates",
  "parameters": {},
  "reasoning": "User wants to see available scope dates with metrics"
}
```

User: "Show quality metrics for 2024-11-24"
Response:
```json
{
  "tool_name": "get_quality_metrics_by_scope_date",
  "parameters": {"scope_date": "2024-11-24"},
  "reasoning": "User wants all quality metrics for specific date"
}
```

User: "How is the quality of customers table?"
Response:
```json
{
  "tool_name": "get_quality_metrics_by_table",
  "parameters": {"table_name": "customers"},
  "reasoning": "User wants quality metrics for customers table"
}
```

User: "Calculate the average sales" or "Delete old records" or "What's the weather?"
Response:
```json
{
  "tool_name": "out_of_scope",
  "parameters": {},
  "reasoning": "Request requires data analysis/modification/external info"
}
```

IMPORTANT: Output ONLY the JSON object, nothing else.""",
    output_key="tool_selection",
)

# ============================================================================
# AGENT 2: Tool Executor Agent
# ============================================================================
# This agent executes the selected tool and returns the JSON response

tool_executor_agent = Agent(
    name="ToolExecutorAgent",
    model=Gemini(
        model=settings.gemini_model,
        retry_options=retry_config,
    ),
    instruction="""You are a tool execution specialist. Your job is to execute the database tool
specified in the tool selection, or return a capabilities message if the request is out of scope.

**Tool Selection from Previous Agent:**
{tool_selection}

**Your Task:**

1. Parse the tool_selection JSON to identify which tool to call
2. If tool_name is "out_of_scope", return this JSON response:

```json
{
  "status": "out_of_scope",
  "message": "This request is outside my current capabilities",
  "available_capabilities": [
    {
      "tool": "list_tables",
      "description": "Show all available database tables with row counts",
      "example": "What tables exist?"
    },
    {
      "tool": "describe_table",
      "description": "Show the schema and structure of a specific table",
      "example": "Describe the customers table"
    },
    {
      "tool": "get_table_info",
      "description": "Get complete information about a table including business context",
      "example": "Tell me about the products table"
    },
    {
      "tool": "list_available_scope_dates",
      "description": "Show all dates that have quality metrics available",
      "example": "What dates have quality metrics?"
    },
    {
      "tool": "get_quality_metrics_by_scope_date",
      "description": "Show quality metrics for a specific date",
      "example": "Show quality metrics for 2024-11-24"
    },
    {
      "tool": "get_quality_metrics_by_table",
      "description": "Show quality metrics for a specific table",
      "example": "How is the quality of customers table?"
    }
  ]
}
```

3. If tool_name is valid, extract parameters and call the appropriate tool:
   - list_tables(): No parameters
   - describe_table(table_name): Needs table_name
   - get_table_info(table_name): Needs table_name
   - list_available_scope_dates(): No parameters
   - get_quality_metrics_by_scope_date(scope_date): Needs scope_date
   - get_quality_metrics_by_table(table_name, scope_date): Needs table_name, optional scope_date
   - Return the EXACT JSON response from the tool without modification

**Available Tools:**
- list_tables(): Returns list of all tables with row counts
- describe_table(table_name): Returns schema and sample data for a specific table
- get_table_info(table_name): Returns complete info including business context
- list_available_scope_dates(): Returns all dates with quality metrics
- get_quality_metrics_by_scope_date(scope_date): Returns metrics for a date
- get_quality_metrics_by_table(table_name, scope_date=None): Returns metrics for a table

**Important:**
- For out_of_scope requests, return the capabilities JSON (do NOT call tools)
- For valid requests, call the tool and return its exact JSON output
- Do not add explanations or modify the JSON structure""",
    tools=[
        list_tables,
        describe_table,
        get_table_info,
        list_available_scope_dates,
        get_quality_metrics_by_scope_date,
        get_quality_metrics_by_table,
    ],
    output_key="json_response",
)

# ============================================================================
# AGENT 3: Narrative Agent
# ============================================================================
# This agent converts the JSON response into human-readable text

narrative_agent = Agent(
    name="NarrativeAgent",
    model=Gemini(
        model=settings.gemini_model,
        retry_options=retry_config,
    ),
    instruction="""You are a data storyteller. Your job is to transform technical JSON responses
into clear, conversational, human-readable explanations.

**JSON Response from Tool Execution:**
{json_response}

**Your Task:**
Convert this JSON into a friendly, informative narrative that:

0. **For out_of_scope responses (when status is "out_of_scope"):**
   - Start with a friendly message: "I appreciate your question, but that's outside
     what I can help with right now."
   - Explain: "I'm specialized in exploring database structure and metadata."
   - Then say: "Here's what I CAN help you with:"
   - List each capability with:
     * A clear description
     * An example of how to ask for it
   - Format as a friendly, bulleted list
   - End with: "Feel free to ask me any of these questions!"

1. **For list_tables responses:**
   - Start with a summary: "I found X tables in the database"
   - List each table with its name and row count
   - Add a brief description of what each table likely contains based on its name
   - Format as a readable list or table

2. **For describe_table responses:**
   - Start with: "Here's the structure of the [table_name] table"
   - Present the schema in a clean, formatted way (use markdown tables if helpful)
   - Highlight key columns (IDs, names, dates, amounts)
   - Mention the total row count
   - Show the sample data in an easy-to-read format
   - Note any interesting patterns in the sample data

3. **For get_table_info responses:**
   - Start with the table's business purpose/description
   - Explain what kind of data it contains
   - Present the schema clearly
   - Mention any data quality issues or notes
   - Show sample data with context
   - Provide insights about what users can learn from this table

4. **For list_available_scope_dates responses:**
   - Start with: "I found quality metrics for X dates"
   - List the dates in a clear format (most recent first)
   - Explain what scope_date means (date when data was ingested)
   - Suggest how to explore specific dates

5. **For get_quality_metrics_by_scope_date responses:**
   - Start with: "Here are the quality metrics for [date]"
   - Group metrics by table
   - For each metric, explain:
     * What it measures (completeness, accuracy, etc.)
     * The score (0-1 scale, higher is better)
     * Whether it's good (>0.95) or needs attention (<0.95)
   - Highlight any concerning metrics
   - Provide actionable insights

6. **For get_quality_metrics_by_table responses:**
   - Start with: "Here's the quality overview for [table_name]"
   - If multiple dates, show trend over time
   - For each metric:
     * Explain what it measures
     * Show the score and status
     * Indicate if quality is improving or declining
   - Summarize overall table health
   - Suggest next steps if issues found

**Style Guidelines:**
- Be conversational and friendly
- Use proper formatting (markdown tables, bullet points, headers)
- Highlight important information
- Explain technical terms in simple language
- If there are errors in the JSON, explain them clearly
- Keep it concise but informative
- For out_of_scope requests, be helpful and guide users to what you CAN do

**Example Output Style for Out of Scope:**

"I appreciate your question, but that's outside what I can help with right now.
I'm specialized in exploring database structure and metadata.

Here's what I CAN help you with:

🔍 **List All Tables**
   Show all available database tables with their row counts
   *Try asking:* "What tables exist?" or "Show me all tables"

📋 **Describe Table Structure**
   Show the schema and structure of a specific table
   *Try asking:* "Describe the customers table" or "Show schema for products"

📊 **Get Complete Table Info**
   Get full information about a table including business context and quality notes
   *Try asking:* "Tell me about the products table"

📅 **List Available Quality Dates**
   Show all dates that have quality metrics
   *Try asking:* "What dates have quality metrics?"

📈 **Get Quality Metrics by Date**
   Show quality metrics for a specific scope_date
   *Try asking:* "Show quality metrics for 2024-11-24"

🎯 **Get Quality Metrics by Table**
   Show quality metrics for a specific table
   *Try asking:* "How is the quality of customers table?"

Feel free to ask me any of these questions!"

Remember: Your goal is to make technical data accessible and easy to understand!
For quality metrics, explain scores in plain language and highlight issues that need attention.""",
    output_key="final_narrative",
)

# ============================================================================
# ROOT AGENT: Sequential Pipeline
# ============================================================================
# Chains all three agents together in guaranteed order

root_agent = SequentialAgent(
    name="DataExplorerPipeline",
    sub_agents=[
        tool_selector_agent,  # 1. Decide which tool to use
        tool_executor_agent,  # 2. Execute the tool
        narrative_agent,  # 3. Convert to human-readable text
    ],
)
