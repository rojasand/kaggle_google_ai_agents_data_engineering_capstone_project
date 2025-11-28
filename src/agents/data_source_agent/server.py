"""A2A Server for Data Source Agent - exposes agent via Agent2Agent protocol."""

import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from src.agents.data_source_agent.agent import root_agent

# Convert agent to A2A-compatible FastAPI app
app = to_a2a(
    root_agent,
    port=8001
)

if __name__ == "__main__":
    print("🚀 Starting Data Source Agent A2A Server...")
    print("📍 Server will be available at: http://localhost:8001")
    print("📋 Agent card: http://localhost:8001/.well-known/agent-card.json")
    print("\nPress CTRL+C to stop the server\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)
