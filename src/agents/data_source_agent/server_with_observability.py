"""A2A Server for Data Source Agent with Observability."""

import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from src.agents.data_source_agent.agent_with_observability import (
    metrics_plugin,
    root_agent,
)

# Convert agent to A2A-compatible FastAPI app
app = to_a2a(root_agent, port=8001)

if __name__ == "__main__":
    print("🚀 Starting Data Source Agent A2A Server with Observability...")
    print("📍 Server will be available at: http://localhost:8001")
    print("📋 Agent card: http://localhost:8001/.well-known/agent-card.json")
    print(f"📊 Metrics plugin: {metrics_plugin.agent_name}")
    print("\nPress CTRL+C to stop the server\n")

    try:
        uvicorn.run(app, host="0.0.0.0", port=8001)
    finally:
        # Save metrics on shutdown
        print("\n📊 Saving metrics...")
        metrics_file = metrics_plugin.save_metrics()
        print(f"✅ Metrics saved to: {metrics_file}")
