"""Data Robot Agent - Hierarchical leader orchestrator for all data tasks.

Architecture:
    - ParallelAgent: Concurrent capability checking (SQL, Quality, Exploration, Ingestion)
    - SequentialAgent: Request parsing → execution → formatting
    - Root Agent: Orchestrates both patterns for comprehensive request handling
"""

from src.agents.data_robot_agent.agent import root_agent, explain_capabilities

__all__ = ["root_agent", "explain_capabilities"]
