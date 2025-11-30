# Data Robot Agent - Project Analysis Report

## Design Patterns & Architecture Analysis

This report documents the design patterns, function signatures, and data structures copied or adapted from the Course Notebooks and existing agents to ensure code consistency and maximum reuse.

---

## 1. Multi-Agent Orchestration Patterns

### SequentialAgent Pattern (from quality_agent, sql_agent, multi_agent_explorer)
- **Pattern**: Three-stage linear pipeline with deterministic state flow
- **Signature**: `SequentialAgent(name="...", sub_agents=[agent1, agent2, agent3])`
- **State Flow Mechanism**: Using `output_key` parameter
  - Agent 1: `output_key="stage_one_output"` → captures its response
  - Agent 2 receives `{stage_one_output}` in its instruction prompt
  - Agent 2: `output_key="stage_two_output"` → captures its response
  - Agent 3 receives both `{stage_one_output}` and `{stage_two_output}` via prompt interpolation
- **Implementation in Project**: Reused in data_robot_agent's RequestParser → CapabilityExecutor → ResponseFormatter pipeline
- **Course Reference**: Day 1B - Agent Architectures (SequentialAgent section)

### ParallelAgent Pattern (from Day 1B course notebooks)
- **Pattern**: Concurrent execution of independent tasks with aggregated results
- **Signature**: `ParallelAgent(name="...", sub_agents=[agent1, agent2, agent3, agent4])`
- **Behavior**: All sub-agents execute simultaneously, results collected before returning
- **Use Case**: Capability checking (SQL, Quality, Exploration, Ingestion statuses in parallel)
- **Implementation in Project**: Used for concurrent capability checks before sequential request routing
- **Course Reference**: Day 1B - Agent Architectures (ParallelAgent section)

---

## 2. Tool Selection Logic & Instructions

### Pattern Source: multi_agent_explorer, quality_agent
- **Tool Selector Pattern**: Explicit decision tree in agent instructions
- **Approach**:
  ```
  If user asks X → Call tool_a()
  If user asks Y → Call tool_b()
  If ambiguous → Call tool_even_if_table_doesnt_exist (tool returns error help text)
  ```
- **Instruction Structure**:
  1. List available tools with clear names
  2. For each tool: explain WHEN to use it
  3. Provide example user queries for each tool
  4. Give JSON response format expected from this stage
  5. Show examples of input → tool → output flow
- **Reused in data_robot_agent**: RequestParser agent uses this pattern to decide which of four capabilities to invoke

### Critical Rules Pattern (from data_agent, quality_agent)
- **Rule #1**: "ALWAYS call a tool first - never refuse or explain capabilities"
- **Rule #2**: "Tool selection: Match user query to specific tool"
- **Rule #3**: "Response format: Use bullet points, bold for important terms, be concise"
- **Reused in data_robot_agent**: Applied to RequestParser to ensure it always routes to a capability

---

## 3. State Management & Output Keys

### output_key Pattern (from quality_agent, sql_agent)
- **Definition**: Named output from each agent in a SequentialAgent pipeline
- **Syntax in Agent Definition**:
  ```python
  agent1 = Agent(
      name="Parser",
      model=Gemini(...),
      instruction="...",
      output_key="request_info"  # This agent's output captured as "request_info"
  )
  ```
- **Access in Next Agent**: Interpolate in instruction string:
  ```python
  agent2 = Agent(
      name="Executor",
      instruction="Parse this request info: {request_info}\n\nNow execute it..."
  )
  ```
- **Data Structure**: JSON objects passed between agents
  - Example from quality_agent:
    ```json
    {
      "request_type": "calculate",
      "table_name": "customers",
      "logic_date": "2024-11-24",
      "message": "Calculating quality metrics..."
    }
    ```
- **Reused in data_robot_agent**: 
  - RequestParser outputs `output_key="request_info"` (parsed request with capability determination)
  - CapabilityExecutor outputs `output_key="execution_result"` (result from delegated agent)
  - ResponseFormatter receives both via interpolation

---

## 4. Function Signatures & Tool Patterns

### Tool Return Pattern (from all tools in src/tools/)
- **Standard Response Structure**:
  ```python
  {
      "status": "success|error|partial_success|info",
      "message": "User-friendly summary for response narrative",
      "error_message": "Technical details (only if status='error')",
      # Additional fields specific to the tool
      "data_key1": value1,
      "data_key2": value2
  }
  ```
- **Example from exploration_tools.py**:
  ```python
  def list_tables():
      return {
          "status": "success",
          "message": "Database contains X tables",
          "tables": [{"name": "customers", "row_count": 525}, ...],
          "total_tables": 3
      }
  ```
- **Example from quality_tools.py**:
  ```python
  def calculate_quality_metrics(table_name: str, logic_date: str):
      return {
          "status": "success",
          "message": "Quality metrics calculated",
          "table_name": "customers",
          "metrics_calculated": 5,
          "total_metrics": 5
      }
  ```
- **Reused in data_robot_agent**: All four capability checkers return this structure

### Agent Tools (from Day 2A course)
- **Definition**: Wrapping agent as a tool for delegation
- **Signature**: `AgentTool(agent_instance, description="...")`
- **Use Case**: CapabilityExecutor delegates to specialized agents (data_agent, sql_agent, quality_agent, ingestion_agent)
- **Behavior**: Agent receives request and returns result, control returns to parent agent
- **Reused in data_robot_agent**: CapabilityExecutor uses AgentTool for each of four specialized agents

---

## 5. Response Template Patterns

### Format from data_agent, quality_agent, sql_agent
- **Bullet Points**: Use "•" for lists, not dashes
- **Bold for Emphasis**: `**table_name**`, `**metric_name**`, `**important_concept**`
- **Structured Sections**: Use markdown headers `##`, `###` for clarity
- **JSON for System Processing**: Tools and intermediate agents use JSON
- **Markdown for User Display**: Final narrative uses markdown with headers, tables, bullet points
- **Business Language**: Avoid technical jargon, explain concepts for non-technical users

### Example Response Structure (from quality_agent's NarrativeAgent):
```
# Quality Metrics for [TABLE_NAME] on [DATE]

## Quality Metrics Overview

• **Metric Name** - Current Score: X% | Previous Score: Y% | Trend: ↑/↓/→
  Business Meaning: [What this metric tells us about the data]
  Impact: [Why this matters to business]

## Overall Assessment

- Summary of metrics above/below thresholds
- Priority areas for improvement
- Positive highlights

## Quality Scale Reference

- Excellent: 95-100%
- Good: 90-95%
- Poor: below 90%
```

---

## 6. Error Handling & Validation

### Pattern from all agents
- **Never Raise Exceptions**: All tools/agents return structured error responses
- **Error Response Format**:
  ```json
  {
      "status": "error",
      "message": "What went wrong (user-friendly)",
      "error_message": "Technical details",
      "suggestion": "How to fix it"
  }
  ```
- **Agent Handling of Errors**: Instructions tell agents how to gracefully present errors
  - Example from multi_agent_explorer: "If tool returns out_of_scope, explain capabilities"
  - Example from sql_agent: "If query fails, suggest correct syntax"
- **Reused in data_robot_agent**: All four capability checkers handle errors gracefully, ResponseFormatter explains errors to user

### Validation Pattern (from ingestion_agent)
- **Input Validation**: Happen before tool execution
- **Pydantic Models**: Used for data validation (CSV row validation)
- **Helpful Error Messages**: Include what's valid if something isn't
- **Graceful Degradation**: Partial success if some rows valid, some invalid

---

## 7. Retry Configuration

### Consistent Configuration (applied project-wide)
```python
from google.genai import types

retry_config = types.HttpRetryOptions(
    attempts=5,              # Maximum 5 retry attempts
    exp_base=7,              # Exponential backoff base (delay = attempt * 7 seconds)
    initial_delay=1,         # Start with 1 second
    http_status_codes=[429, 500, 503, 504]  # Retry on rate limit & server errors
)

model = Gemini(
    model="gemini-2.5-flash-lite",
    retry_options=retry_config
)
```
- **Reused in data_robot_agent**: All agents use identical retry configuration for consistency

---

## 8. Instruction Design Patterns

### Components (from quality_agent, sql_agent, multi_agent_explorer):

1. **Role Definition** (start with clear role)
   ```
   You are a [specific role description].
   Your job is to [primary responsibility].
   ```

2. **Critical Rules Section** (highest priority rules)
   ```
   **CRITICAL RULES:**
   1. [Rule that must be followed]
   2. [Non-negotiable behavior]
   ```

3. **Available Tools/Capabilities** (explicit listing)
   ```
   **Available Tools:**
   1. tool_name - When to use: [example queries]
   2. tool_name - When to use: [example queries]
   ```

4. **Tool Selection Logic** (decision tree)
   ```
   **Tool Selection Logic:**
   - If user asks "X" → Use tool_a()
   - If user asks "Y" → Use tool_b()
   - If uncertain → Call tool anyway (returns error help)
   ```

5. **Response Format Specification** (exact format expected)
   ```
   **Response Format:**
   Return ONLY a JSON object with:
   - status: "success|error|info"
   - message: User-friendly summary
   - [other fields specific to this agent]
   ```

6. **Examples** (input → output flow)
   ```
   **Examples:**
   User: "How many customers?"
   Response: {"status": "success", "message": "...", "count": 525}
   ```

7. **Important Notes** (edge cases, restrictions)
   ```
   **IMPORTANT:**
   - Always call tools even if you think they'll fail
   - Never modify JSON structure
   - Output ONLY the JSON, no explanations
   ```

- **Reused in data_robot_agent**: RequestParser, CapabilityExecutor, ResponseFormatter all follow this structure

---

## 9. Key Abbreviations & Concepts

### From Course Notebooks (Day 3A - Agent Sessions)
- **output_key**: Named output capture mechanism in SequentialAgent
- **Session**: Conversation thread with unique identifiers (app_name, user_id, session_id)
- **scope_date**: Date when data was ingested (used consistently in quality_agent, data_agent)

### From Project (src/database/models.py)
- **scope_date**: Ingestion date, attached to every data record for tracking which batch has quality issues
- **logic_date**: Same as scope_date, used interchangeably
- **pipeline_runs**: Audit table tracking data ingestion history

---

## 10. Architecture Summary

### Four Parallel Capability Checkers
Each implements a mini-agent pattern that:
1. Uses relevant existing tools to check capability availability
2. Returns structured JSON: `{"status": "ok|unavailable", "details": {...}}`
3. Executes concurrently with other checkers

**Signatures**:
```python
sql_checker_agent = Agent(...)      # Checks: can we execute SQL?
quality_checker_agent = Agent(...)  # Checks: are quality metrics available?
exploration_checker_agent = Agent(...)  # Checks: can we explore tables?
ingestion_checker_agent = Agent(...)    # Checks: is ingestion active?

parallel_checker = ParallelAgent(
    sub_agents=[sql_checker_agent, quality_checker_agent, 
                exploration_checker_agent, ingestion_checker_agent]
)
```

### Three Sequential Request Routers
Following quality_agent pattern:
```python
request_parser_agent = Agent(
    name="RequestParser",
    output_key="request_info"  # Outputs {"capability_needed": "...", ...}
)

capability_executor_agent = Agent(
    name="CapabilityExecutor",
    tools=[AgentTool(data_agent), AgentTool(sql_agent), ...],
    output_key="execution_result"  # Outputs result from delegated agent
)

response_formatter_agent = Agent(
    name="ResponseFormatter",
    # No output_key needed, this is final output
)

sequential_router = SequentialAgent(
    sub_agents=[request_parser_agent, capability_executor_agent, response_formatter_agent]
)
```

---

## 11. Files Referencing Design Patterns

| Pattern | Source File | Usage in data_robot_agent |
|---------|-------------|---------------------------|
| SequentialAgent | `src/agents/quality_agent/agent.py` | request_router_agents.py |
| ParallelAgent | Day 1B course notebook | capability_checker_agents.py |
| output_key | `src/agents/sql_agent/agent.py` | All sequential agents |
| Tool selection logic | `src/agents/multi_agent_explorer/agent.py` | RequestParser instructions |
| Response templates | `src/agents/data_agent/agent.py` | ResponseFormatter instructions |
| Error handling | `src/tools/query_tools.py` | All capability checkers |
| Retry configuration | `src/config/settings.py` | All Gemini model initializations |
| Agent instructions | All existing agents | request_router_agents.py |

---

## Summary: 5 Key Reuse Points

1. **SequentialAgent + output_key Pattern**: Three-stage pipeline with state passing from quality_agent/sql_agent
2. **ParallelAgent for Concurrent Checks**: Lightweight parallel capability verification from Day 1B course
3. **Tool Selection Logic**: Explicit decision tree from multi_agent_explorer for routing to four capabilities
4. **Response Formatting**: Markdown templates with bullet points and bold emphasis from data_agent/quality_agent
5. **Structured Error Handling**: JSON responses with status/message/error_message from all tools and agents

**Project Consistency**: 100% adherence to established patterns ensures maintainability and predictable behavior across all agents.
