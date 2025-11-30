# Data Robot Agent - Quick Start Guide

## ⚡ 5-Minute Quick Start

### Step 1: Validate the Agent (30 seconds)
```bash
poetry run python validate_agent.py
```

Expected output:
```
✅ PASS: Agent Structure Validation
✅ PASS: Capabilities Documentation
✅ PASS: Architecture Validation
✅ PASS: Agent Operational Status

✅ ALL VALIDATION CHECKS PASSED!
```

### Step 2: Start the Server (2 minutes)
```bash
poetry run python src/agents/data_robot_agent/server.py
```

Expected output:
```
🚀 Starting Data Robot Agent A2A Server...
📍 Server will be available at: http://localhost:8002
📋 Agent card: http://localhost:8002/.well-known/agent-card.json
```

### Step 3: Test in Browser (2 minutes)
1. Open: `http://localhost:8002`
2. Click "Start Conversation"
3. Try a query:
   ```
   What tables are available?
   ```

That's it! The agent is working! 🎉

---

## 🧪 What to Test

### Test 1: Data Exploration (Table Discovery)
```
Query: "What tables are available?"
Expected: List of tables (customers, products, sales_transactions)
Time: ~50 seconds
```

### Test 2: SQL Query
```
Query: "Show me top 5 customers by name"
Expected: SQL executed, results returned with 5 customer records
Time: ~55 seconds
```

### Test 3: Data Quality
```
Query: "What is the data quality status?"
Expected: Quality metrics for each table
Time: ~50 seconds
```

### Test 4: Data Exploration with Details
```
Query: "Describe the customers table"
Expected: Table structure with column names and types
Time: ~50 seconds
```

### Test 5: Complex Query
```
Query: "How many customers purchased products in the last month?"
Expected: SQL query with count result
Time: ~55 seconds
```

---

## 📊 Understanding the Response Times

The agent uses a **two-stage architecture**:

1. **Stage 1 (Parallel)**: 30-40 seconds
   - Checks 4 capabilities simultaneously
   - SQL capability check
   - Quality capability check
   - Exploration capability check
   - Ingestion capability check

2. **Stage 2 (Sequential)**: 10-20 seconds
   - Parses your request
   - Routes to appropriate specialist agent
   - Formats response

**Total**: 40-60 seconds per query

This is **normal and expected** - the thorough analysis ensures accurate responses.

---

## 🏗️ Architecture at a Glance

```
Your Query
    ↓
data_robot (Root Agent)
    ├─ Delegates to Stage 1: CapabilityChecker (checks all 4 in parallel)
    └─ Delegates to Stage 2: RequestRouter (parses → routes → formats)
        ├─ Routes to SQL Agent (if SQL query)
        ├─ Routes to Quality Agent (if quality analysis)
        ├─ Routes to Exploration Agent (if table/structure questions)
        └─ Routes to Ingestion Agent (if data loading)
    ↓
Formatted Response with Data & Insights
```

---

## 🎯 Four Core Capabilities

| # | Capability | Ask For | Example |
|---|-----------|---------|---------|
| 1 | **SQL** | Natural language queries | "Top 10 customers by revenue" |
| 2 | **Quality** | Data quality analysis | "How complete is the data?" |
| 3 | **Exploration** | Database structure | "What tables exist?" |
| 4 | **Ingestion** | Load data | "Load customer CSV file" |

---

## 🔍 Troubleshooting

### Q: Agent not responding
**A**: Check if server is running on port 8002 with `lsof -i :8002`

### Q: "Connection refused" error
**A**: Start the server first: `poetry run python src/agents/data_robot_agent/server.py`

### Q: Response takes too long
**A**: This is normal! Two-stage processing takes 40-60 seconds. This ensures thorough analysis.

### Q: Getting empty responses
**A**: Refresh the page and try a simpler query first like "What tables exist?"

### Q: Server crashes
**A**: Check logs and ensure DuckDB database file exists at `database/data.duckdb`

---

## 📝 Test Checklist

- [ ] Validation passes (4/4 tests)
- [ ] Server starts without errors
- [ ] Browser connects to `http://localhost:8002`
- [ ] "What tables are available?" returns table list
- [ ] "Show me top 5 customers" executes SQL
- [ ] "What is the data quality?" returns quality metrics
- [ ] "Describe customers table" shows table structure
- [ ] Complex queries work correctly

---

## 📚 Detailed Documentation

For more information, see:
- `TEST_REPORT.md` - Full validation results
- `AGENT_FIX_REPORT.md` - Technical details of the fix
- `ADK_WEB_USAGE_GUIDE.md` - Advanced usage patterns
- `src/agents/data_robot_agent/agent.py` - Source code with inline docs

---

## ✨ Key Points

1. ✅ **Ready to Use**: No configuration needed
2. ✅ **Tested**: All 4 capabilities validated
3. ✅ **Safe**: Queries are validated before execution
4. ✅ **Insightful**: Responses include business insights
5. ✅ **Extensible**: Add new capabilities easily

---

## 🚀 Next Steps

1. **Now**: Start the server and test basic queries
2. **Next**: Try multi-turn conversations (agent maintains context)
3. **Later**: Integrate with other systems via A2A protocol

**Start now**: `poetry run python src/agents/data_robot_agent/server.py`

Happy analyzing! 🤖
