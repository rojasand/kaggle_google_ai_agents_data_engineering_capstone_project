"""SQL Agent module."""

from google.adk.apps.app import App, ResumabilityConfig

from src.agents.sql_agent.agent import root_agent

# Create App instance with resumability for web ADK
# This enables pause/resume flow for row limit confirmation
sql_agent_app = App(
    name="sql_agent",
    root_agent=root_agent,
    resumability_config=ResumabilityConfig(is_resumable=True),
)

__all__ = ["root_agent", "sql_agent_app"]
