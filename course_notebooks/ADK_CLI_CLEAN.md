# ADK CLI Reference

Command-line reference for the Google Agent Development Kit (ADK).

## Commands Overview

- `adk create` - Create a new agent
- `adk web` - Start web UI server  
- `adk api_server` - Start API server
- `adk run` - Run interactive CLI
- `adk eval` - Evaluate agents
- `adk deploy` - Deploy to cloud

---

## adk web

Starts a FastAPI server with Web UI for agents.

**Usage:**
```bash
adk web [OPTIONS] [AGENTS_DIR]
```

**Arguments:**
- `AGENTS_DIR` - Optional. Directory of agents (each subdirectory = one agent with `agent.py` and `root_agent`)

**Key Options:**
- `--host <host>` - Binding host (default: `127.0.0.1`)
- `--port <port>` - Server port (default: `8000`)
- `--log_level <level>` - DEBUG | INFO | WARNING | ERROR | CRITICAL
- `--reload` / `--no-reload` - Enable auto-reload
- `--session_service_uri <uri>` - Session storage (sqlite:// or agentengine://)

**Example:**
```bash
# Run from agents directory
cd agents && adk web --port 8000

# Or specify agents directory
adk web --port 8000 path/to/agents
```

---

## adk api_server

Starts a FastAPI REST API server for agents.

**Usage:**
```bash
adk api_server [OPTIONS] [AGENTS_DIR]
```

**Arguments:**
- `AGENTS_DIR` - Optional. Directory containing agent subdirectories

**Key Options:**
- `--host <host>` - Binding host (default: `127.0.0.1`)
- `--port <port>` - Server port
- `--a2a` - Enable Agent-to-Agent protocol endpoint
- `--session_service_uri <uri>` - Session persistence
- `--memory_service_uri <uri>` - Memory service (rag:// or agentengine://)

**Example:**
```bash
adk api_server --host 0.0.0.0 --port 8000 agents/
```

---

## adk create

Creates a new agent with template structure.

**Usage:**
```bash
adk create [OPTIONS] APP_NAME
```

**Arguments:**
- `APP_NAME` - Required. Name/path for new agent directory

**Options:**
- `--model <model>` - Model for root agent (default: gemini-2.0-flash-exp)
- `--api_key <key>` - Google AI API Key
- `--project <project>` - Google Cloud project (for Vertex AI)
- `--region <region>` - Google Cloud region

**Example:**
```bash
adk create my_agent --model gemini-2.0-flash-exp
```

**Creates:**
```
my_agent/
  ├── agent.py          # Agent definition with root_agent
  ├── __init__.py       # Package initialization
  ├── .env              # Environment variables
  └── requirements.txt  # Dependencies
```

---

## adk run

Runs an interactive CLI session with an agent.

**Usage:**
```bash
adk run [OPTIONS] AGENT
```

**Arguments:**
- `AGENT` - Required. Path to agent directory

**Options:**
- `--save_session` - Save session to JSON on exit
- `--session_id <id>` - Session ID for saving
- `--resume <file>` - Resume from saved session JSON
- `--replay <file>` - Replay queries from JSON

**Example:**
```bash
# Interactive mode
adk run agents/my_agent

# Save session
adk run --save_session --session_id test_123 agents/my_agent

# Resume previous session
adk run --resume session_123.json agents/my_agent
```

---

## adk eval

Evaluates agent performance using test sets.

**Usage:**
```bash
adk eval [OPTIONS] AGENT_MODULE_FILE_PATH [EVAL_SET_FILE_PATH]...
```

**Arguments:**
- `AGENT_MODULE_FILE_PATH` - Required. Path to agent's `__init__.py` (containing root_agent)
- `EVAL_SET_FILE_PATH` - Optional. One or more `*.evalset.json` files

**Options:**
- `--config_file_path <path>` - Path to test config (criteria thresholds)
- `--print_detailed_results` - Show detailed turn-by-turn results
- `--eval_storage_uri <uri>` - GCS bucket for storing results (gs://)

**Example:**
```bash
# Run all evals
cd agents/my_agent
adk eval . basic_tests.evalset.json --config_file_path=test_config.json --print_detailed_results

# Run specific evals from file
adk eval . tests.evalset.json:eval_1,eval_2,eval_3 --config_file_path=config.json
```

**Files Required:**
- `test_config.json` - Evaluation criteria and thresholds
- `*.evalset.json` - Test cases with expected responses

---

## Important Notes

### Agent Directory Structure

For `adk web` and `adk api_server` to discover agents:

```
agents/                    # AGENTS_DIR argument
  ├── agent_one/           # Agent subdirectory
  │   ├── agent.py         # Must export root_agent
  │   ├── __init__.py      # Package init
  │   └── .env             # Optional env vars
  └── agent_two/
      ├── agent.py
      └── __init__.py
```

When running from `agents/` directory:
```bash
cd agents && adk web
# Discovers: agent_one, agent_two
```

### Session Service URIs

- **SQLite**: `sqlite:///path/to/db.sqlite`
- **PostgreSQL**: `postgresql://user:pass@host:port/dbname`
- **Agent Engine**: `agentengine://<resource_id>`

### Memory Service URIs

- **Vertex AI RAG**: `rag://<rag_corpus_id>`
- **Memory Bank**: `agentengine://<resource_id>`

### Artifact Service URIs

- **Google Cloud Storage**: `gs://<bucket_name>`

---

## Quick Reference

| Task | Command |
|------|---------|
| Create new agent | `adk create my_agent` |
| Test locally (Web UI) | `cd agents && adk web` |
| Test locally (API) | `cd agents && adk api_server` |
| Interactive CLI | `adk run agents/my_agent` |
| Run evaluations | `cd agents/my_agent && adk eval . tests.evalset.json --config_file_path=config.json` |

---

## Common Patterns

### Development Workflow
```bash
# 1. Create agent
adk create my_agent

# 2. Develop and test with web UI
cd my_agent/../  # Go to parent of agent
adk web --port 8000

# 3. Run evaluations
cd my_agent
adk eval . basic_tests.evalset.json --print_detailed_results
```

### Production Setup
```bash
# API server with persistent sessions
adk api_server \
  --host 0.0.0.0 \
  --port 8080 \
  --session_service_uri sqlite:///sessions.db \
  --memory_service_uri agentengine://12345 \
  agents/
```

---

For more details, visit: https://google.github.io/adk-docs/
