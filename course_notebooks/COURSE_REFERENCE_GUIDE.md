# Kaggle Google AI Agents Course - Quick Reference Guide

## Overview
This document provides a synthesized summary of all course notebooks for the Kaggle 5-Day AI Agents Course using Google's Agent Development Kit (ADK). Use this guide to quickly locate which notebook covers specific topics when you need to investigate further.

---

## Day 1: Foundation Concepts

### Day 1A: From Prompt to Action (`day-1a-from-prompt-to-action.ipynb`)

**Core Concept**: Introduction to AI Agents and basic agent creation

**Key Topics**:
- **What is an AI Agent?**: Agents can think, take actions, and observe results (vs. simple LLM prompts)
- **First Agent Creation**: Building a simple agent with Google Search capability
- **ADK Setup**: Installing google-adk, configuring Gemini API keys
- **Agent Components**:
  - `name` and `description`: Agent identification
  - `model`: Gemini 2.5 Flash Lite LLM
  - `instruction`: Agent's guiding prompt
  - `tools`: Available capabilities (e.g., google_search)
- **Runner**: Using `InMemoryRunner` to execute agents with `run_debug()`
- **ADK Web Interface**: Using `adk create` and `adk web` for interactive testing
- **Retry Configuration**: Handling rate limits and transient errors with exponential backoff

**When to Reference**: Starting with ADK, understanding agent basics, setting up your first agent, using the web UI

---

### Day 1B: Agent Architectures (`day-1b-agent-architectures.ipynb`)

**Core Concept**: Multi-agent systems and workflow orchestration patterns

**Key Topics**:
- **Multi-Agent Systems**: Specialized agents collaborating vs. single do-it-all agent
- **LLM Orchestrator Pattern**: Using an LLM as a "manager" to dynamically decide which sub-agent to call
- **Sequential Workflows**: Deterministic pipeline (A → B → C) using `SequentialAgent`
  - Use case: Outline → Write → Edit
  - Passing state with `output_key`
- **Parallel Workflows**: Concurrent execution of independent tasks using `ParallelAgent`
  - Use case: Multi-topic research (Tech, Health, Finance simultaneously)
  - Aggregating results after parallel completion
- **Loop Workflows**: Iterative refinement using `LoopAgent`
  - Use case: Writer + Critic refinement cycle
  - Exit conditions: `max_iterations` or calling `exit_loop()` function
  - Using `FunctionTool` for loop control
- **Decision Tree**: Choosing the right pattern for your use case

**When to Reference**: Designing multi-step workflows, orchestrating multiple agents, iterative improvement patterns, state management between agents

---

## Day 2: Agent Tools

### Day 2A: Agent Tools (`day-2a-agent-tools.ipynb`)

**Core Concept**: Building custom tools and multi-tool agents

**Key Topics**:
- **Why Tools?**: Agents need tools to access external data and take actions
- **Function Tools**: Converting Python functions to agent tools
  - Example: `get_fee_for_payment_method()`, `get_exchange_rate()`
  - Structured responses with status fields
  - Input validation and error handling
- **Code Execution**: Using `BuiltInCodeExecutor` for reliable calculations
  - Gemini's Code Execution capability
  - Math operations via generated Python code
- **Agent Tools**: Using agents as tools with `AgentTool`
  - Example: Currency agent using calculation agent as a tool
  - Delegation for specific tasks
- **Agent Tools vs Sub-Agents**:
  - Agent Tools: Delegation with control return
  - Sub-Agents: Complete control transfer
- **ADK Tool Categories**:
  - **Custom Tools**: Function Tools, Long Running Function Tools, Agent Tools, MCP Tools, OpenAPI Tools
  - **Built-in Tools**: Gemini Tools (google_search, BuiltInCodeExecutor), Google Cloud Tools, Third-party Tools

**When to Reference**: Creating custom functions, code execution, multi-tool coordination, understanding tool types

---

### Day 2B: Agent Tools Best Practice (`day-2b-agent-tools-best-practice.ipynb`)

**Core Concept**: Advanced tool patterns - MCP integration and long-running operations

**Key Topics**:
- **MCP (Model Context Protocol) Integration**:
  - Connecting to external MCP servers (filesystem, time, databases)
  - Using `McpToolset` with stdio transport
  - Community-maintained MCP servers
  - Example: Time service with multiple capabilities
- **Long-Running Operations (LRO)**:
  - Operations requiring human-in-the-loop approval
  - Using `ToolContext.request_confirmation()`
  - Pausing and resuming agent execution
  - Example: Shipping order approval workflow
- **Resumable Workflows**:
  - `App` with `ResumabilityConfig(is_resumable=True)`
  - `Runner` with session and app configuration
  - Detecting pause with `adk_request_confirmation` event
  - Using `invocation_id` to resume execution
- **Event Handling**:
  - Processing events from `run_async()`
  - Checking for approval requests
  - Creating approval responses with `FunctionResponse`
- **Workflow Patterns**: Initial call → Detect pause → Get human input → Resume with same invocation_id

**When to Reference**: External service integration, approval workflows, human-in-the-loop patterns, pausing/resuming agents, MCP server setup

---

## Day 3: Memory Management

### Day 3A: Agent Sessions (`day-3a-agent-sessions.ipynb`)

**Core Concept**: Managing conversation state and context across multiple turns

**Key Topics**:
- **Sessions**: Conversation threads with unique identifiers (app_name, user_id, session_id)
- **Events**: Records of everything that happens (user messages, agent responses, tool calls)
- **Session Management**:
  - `InMemorySessionService`: Development/testing (non-persistent)
  - `DatabaseSessionService`: Production (persistent with SQLite/PostgreSQL)
  - Creating sessions before running agents
- **Runner Patterns**:
  - `run_debug()`: Quick prototyping (auto-creates session)
  - `run_async()`: Production (manual session management, streaming)
- **Context Engineering**:
  - **Context Compaction**: Automatic summarization with `EventsCompactionConfig`
  - `compaction_interval`: Trigger after n invocations
  - `overlap_size`: Retain previous turns for context
  - Reducing token usage and costs
- **Session State Management**:
  - Custom tools accessing `tool_context.state`
  - Key prefixes: `user:`, `app:`, `temp:`
  - Storing structured data during conversations
  - Session isolation by default
- **Context Caching**: Reducing token size of static instructions

**When to Reference**: Multi-turn conversations, session persistence, context management, database integration, state tracking

---

### Day 3B: Agent Memory (`day-3b-agent-memory.ipynb`)

**Core Concept**: Long-term knowledge storage across multiple conversations

**Key Topics**:
- **Session vs Memory**:
  - Session: Short-term (single conversation)
  - Memory: Long-term (across multiple conversations)
- **Memory Capabilities**:
  - Cross-conversation recall
  - Intelligent extraction with LLM-powered consolidation
  - Semantic search (meaning-based retrieval)
  - Persistent storage
- **Memory Service Setup**:
  - `InMemoryMemoryService`: Learning/testing (keyword matching)
  - `VertexAiMemoryBankService`: Production (semantic search, persistent)
  - Initializing alongside session service
- **Storing Memories**:
  - `add_session_to_memory()`: Transfer session data to memory
  - Manual calls vs automated with callbacks
- **Retrieving Memories**:
  - **Reactive Pattern**: `load_memory` tool (agent decides when)
  - **Proactive Pattern**: `preload_memory` tool (always loads)
  - Manual search with `search_memory()`
- **Callbacks**:
  - `after_agent_callback`: Automatic memory storage
  - Accessing memory service via `callback_context`
  - Available callback types: before/after agent, tool, model
- **Memory Consolidation**:
  - Extracting key facts vs storing raw conversations
  - LLM-powered analysis and deduplication
  - Managed by production memory services

**When to Reference**: Cross-session memory, user preferences, automatic memory storage, semantic search, callbacks, consolidation

---

## Day 4: Observability and Evaluation

### Day 4A: Agent Observability (`day-4a-agent-observability.ipynb`)

**Core Concept**: Debugging and monitoring agent behavior through logs, traces, and metrics

**Key Topics**:
- **Observability Pillars**:
  - **Logs**: What happened (single events)
  - **Traces**: Why it happened (execution sequence)
  - **Metrics**: How well it performs (aggregated data)
- **Development Debugging**:
  - `adk web --log_level DEBUG`
  - Real-time UI with execution traces
  - Inspecting LLM requests/responses and tool calls
- **Logging Configuration**:
  - Setting up `logging.basicConfig()` with DEBUG level
  - File-based logging for persistent records
  - Cleaning up old log files
- **Plugins and Callbacks**:
  - **Plugin**: Custom code module running at lifecycle stages
  - **Callbacks**: Python functions triggered at specific points
  - Callback types: before/after agent, tool, model, on_model_error
  - Example: `CountInvocationPlugin` tracking invocations
- **Production Logging**:
  - `LoggingPlugin()`: Built-in comprehensive logging
  - Automatic capture of messages, timing, LLM requests, tool calls
  - Registering plugins with `Runner(plugins=[LoggingPlugin()])`
- **When to Use What**:
  - Development: ADK web UI + DEBUG logs
  - Production: LoggingPlugin
  - Custom needs: Build custom plugins/callbacks

**When to Reference**: Debugging failures, production monitoring, performance analysis, custom logging requirements, plugin development

---

### Day 4B: Agent Evaluation (`day-4b-agent-evaluation.ipynb`)

**Core Concept**: Proactive testing and quality assurance for agents

**Key Topics**:
- **Agent Evaluation vs Testing**:
  - Traditional testing: Happy path scenarios
  - Agent evaluation: Non-deterministic behavior, trajectory analysis
- **Evaluation in ADK Web UI**:
  - Interactive test creation
  - Eval sets: Collections of test cases
  - Running evaluations and analyzing results
  - Downloading evalsets for CI/CD
- **Evaluation Criteria**:
  - `tool_trajectory_avg_score`: Tool usage correctness
  - `response_match_score`: Text similarity threshold
  - Pass/fail thresholds
- **Evaluation Files**:
  - `test_config.json`: Evaluation criteria configuration
  - `*.evalset.json`: Test cases with expected results
  - Structure: eval_id, user_content, final_response, intermediate_data (tool_uses)
- **CLI Evaluation**:
  - `adk eval` command for automated testing
  - `--config_file_path`: Specify criteria
  - `--print_detailed_results`: Turn-by-turn breakdown
- **Result Analysis**:
  - Identifying root causes (tool vs response issues)
  - Actionable insights for agent improvement
  - Regression detection
- **User Simulation** (Advanced):
  - Dynamic prompt generation with LLM
  - `ConversationScenario` with conversation plans
  - Testing unpredictable conversation flows
- **Advanced Criteria**: `safety_v1`, `hallucinations_v1` (requires Google Cloud)

**When to Reference**: Testing agent quality, regression detection, CI/CD integration, analyzing failures, user simulation

---

## Day 5: Advanced Topics

### Day 5A: Agent2Agent Communication (`day-5a-agent2agent-communication.ipynb`)

**Core Concept**: Multi-agent systems communicating across networks using A2A protocol

**Key Topics**:
- **A2A (Agent2Agent) Protocol**:
  - Standard for agent communication over networks
  - Language/framework agnostic
  - Formal contracts via agent cards
- **A2A Use Cases**:
  - Cross-Framework: ADK agent with other frameworks
  - Cross-Language: Python agent calling Java/Node.js agent
  - Cross-Organization: Internal agent + external vendor services
- **A2A vs Local Sub-Agents**:
  - A2A: External services, different organizations, network communication
  - Local: Same codebase, same machine, low latency
- **Exposing Agents via A2A**:
  - `to_a2a(agent)`: Creates A2A-compatible server
  - Returns FastAPI app with `/tasks` endpoint
  - Auto-generated agent card at `/.well-known/agent-card.json`
  - Running with `uvicorn` on specific ports
- **Consuming Remote Agents**:
  - `RemoteA2aAgent`: Client-side proxy
  - Points to agent card URL
  - Uses like local sub-agent
  - ADK handles protocol details
- **Architecture Example**: Product Catalog Agent (vendor) + Customer Support Agent (consumer)
- **Communication Flow**:
  - Consumer calls RemoteA2aAgent
  - HTTP POST to `/tasks` endpoint
  - A2A protocol JSON format
  - Response returned to consumer
- **Agent Cards**: JSON metadata describing agent capabilities (name, description, skills)

**When to Reference**: Microservices architectures, external integrations, vendor agent consumption, cross-language systems, distributed agents

---

## Quick Topic Lookup

| **Topic** | **Primary Notebook(s)** | **Related Notebooks** |
|-----------|------------------------|----------------------|
| **Getting Started** | Day 1A | - |
| **Basic Agent Creation** | Day 1A | - |
| **Multi-Agent Systems** | Day 1B | Day 5A (A2A) |
| **Workflow Patterns** | Day 1B | - |
| **Custom Functions** | Day 2A | Day 2B (LRO) |
| **Code Execution** | Day 2A | - |
| **MCP Integration** | Day 2B | - |
| **Long-Running Operations** | Day 2B | - |
| **Human-in-the-Loop** | Day 2B | - |
| **Sessions** | Day 3A | Day 3B |
| **Memory** | Day 3B | Day 3A |
| **Context Management** | Day 3A | Day 3B |
| **State Management** | Day 3A | - |
| **Callbacks** | Day 3B, Day 4A | - |
| **Plugins** | Day 4A | - |
| **Debugging** | Day 4A | - |
| **Logging** | Day 4A | - |
| **Testing/Evaluation** | Day 4B | - |
| **A2A Protocol** | Day 5A | - |
| **Remote Agents** | Day 5A | - |

---

## Key ADK Components Reference

### Agents
- `Agent` / `LlmAgent`: Basic agent with LLM
- `SequentialAgent`: Linear workflow (A → B → C)
- `ParallelAgent`: Concurrent execution
- `LoopAgent`: Iterative refinement
- `RemoteA2aAgent`: Proxy for remote A2A agents

### Tools
- `FunctionTool`: Python function as tool
- `AgentTool`: Use agent as tool
- `McpToolset`: MCP server integration
- `google_search`: Built-in Google Search
- `BuiltInCodeExecutor`: Code execution

### Runtime
- `Runner`: Agent execution manager
- `InMemoryRunner`: Simple execution for prototyping
- `App`: Wrapper for resumability
- `ResumabilityConfig`: Enable pause/resume

### Services
- `InMemorySessionService`: Development sessions
- `DatabaseSessionService`: Persistent sessions
- `InMemoryMemoryService`: Testing memory
- `VertexAiMemoryBankService`: Production memory

### Context & Configuration
- `ToolContext`: Access to state, confirmation requests
- `EventsCompactionConfig`: Context summarization
- `HttpRetryOptions`: Retry configuration
- `LoggingPlugin`: Production logging

### A2A
- `to_a2a()`: Expose agent via A2A
- Agent cards: JSON metadata at `/.well-known/agent-card.json`
- Protocol: HTTP POST to `/tasks` endpoint

---

## Common Patterns

### 1. Basic Agent Setup
```
1. Configure API key and retry options
2. Create agent with model, instruction, tools
3. Create runner (InMemoryRunner or Runner)
4. Execute with run_debug() or run_async()
```

### 2. Multi-Turn Conversation
```
1. Create SessionService (Database for persistence)
2. Create session before running
3. Use run_async() with session identifiers
4. Events stream back responses
```

### 3. Long-Running Operation
```
1. Tool calls request_confirmation() when needed
2. Tool returns and agent pauses
3. Workflow detects adk_request_confirmation event
4. Get human decision
5. Resume with same invocation_id
```

### 4. Memory Across Sessions
```
1. Initialize MemoryService alongside SessionService
2. Transfer: add_session_to_memory()
3. Retrieve: load_memory or preload_memory tools
4. Automate: Use after_agent_callback
```

### 5. Production Observability
```
1. Add LoggingPlugin to runner
2. Configure logging.basicConfig()
3. Monitor logs for issues
4. Use adk web for interactive debugging
```

### 6. Evaluation Pipeline
```
1. Create test_config.json with criteria
2. Create *.evalset.json with test cases
3. Run: adk eval <agent_dir> <evalset> --config_file_path
4. Analyze results and iterate
```

---

## Common Troubleshooting

| **Issue** | **Check Notebook** | **Section** |
|-----------|-------------------|-------------|
| Agent not using tools | Day 1A, Day 4A | Instructions, tool availability, logs |
| Memory not persisting | Day 3A, Day 3B | DatabaseSessionService, add_session_to_memory |
| Context too long | Day 3A | EventsCompactionConfig |
| Agent fails unpredictably | Day 4A | LoggingPlugin, DEBUG logs |
| Poor evaluation scores | Day 4B | Criteria thresholds, agent instructions |
| A2A connection fails | Day 5A | Server running, agent card URL, ports |

---

## Best Practices Summary

1. **Start Simple**: Begin with single agent, add complexity as needed
2. **Use Appropriate Services**: InMemory for dev, Database/Cloud for production
3. **Structured State**: Use key prefixes (user:, app:, temp:) for state management
4. **Automate Memory**: Use callbacks for automatic memory storage
5. **Comprehensive Testing**: Create evalsets early, run frequently
6. **Observability First**: Add LoggingPlugin before production
7. **Choose Right Pattern**: Sequential for pipelines, Parallel for independent tasks, Loop for refinement
8. **A2A for External**: Use A2A for cross-org/cross-language, local sub-agents otherwise
9. **Context Management**: Enable compaction for long conversations
10. **Error Handling**: Configure retry options for reliability

---

## External Resources

- **ADK Documentation**: https://google.github.io/adk-docs/
- **A2A Protocol**: https://a2a-protocol.org/
- **Kaggle Discord**: https://discord.com/invite/kaggle
- **Gemini API**: https://ai.google.dev/gemini-api/docs
- **Google AI Studio**: https://aistudio.google.com/

---

*This reference guide covers all topics from the Kaggle 5-Day AI Agents Course. Use the notebook names and section references to quickly locate detailed information on any topic.*
