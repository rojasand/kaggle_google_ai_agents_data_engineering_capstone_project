"""Observability plugin for tracking agent metrics and logging."""

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.plugins import BasePlugin

from src.config import settings


def setup_logging(agent_name: str = "agent") -> logging.Logger:
    """
    Configure structured logging for agents.

    Args:
        agent_name: Name of the agent for the log file

    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    settings.ensure_directories()

    # Create logger
    logger = logging.getLogger(agent_name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler - detailed logs
    log_file = settings.log_dir / f"{agent_name}_{datetime.now():%Y%m%d_%H%M%S}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Console handler - less verbose
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized for {agent_name}")
    logger.info(f"Log file: {log_file}")

    return logger


class DataMetricsPlugin(BasePlugin):
    """
    Custom plugin to track data generation metrics and agent performance.

    This plugin tracks:
    - Tool invocation counts and latency
    - Data generation statistics (rows, tables, dates)
    - Error rates and types
    - Agent execution flow
    """

    def __init__(self, agent_name: str = "data_source_agent"):
        """
        Initialize the metrics plugin.

        Args:
            agent_name: Name of the agent for logging
        """
        super().__init__(name=f"{agent_name}_metrics")
        self.agent_name = agent_name
        self.logger = setup_logging(agent_name)

        # Metrics storage
        self.tool_counts = defaultdict(int)
        self.tool_errors = defaultdict(int)
        self.tool_timings = defaultdict(list)
        self.data_stats = {
            "tables_generated": defaultdict(int),
            "total_rows": 0,
            "logic_dates": set(),
            "successful_generations": 0,
            "failed_generations": 0,
        }

        # Session tracking
        self.session_start_time = datetime.now()
        self.total_invocations = 0

        self.logger.info(f"DataMetricsPlugin initialized for {agent_name}")

    def before_agent(self, callback_context: CallbackContext) -> None:
        """Called before agent processes user input."""
        self.total_invocations += 1
        user_message = callback_context.user_message

        self.logger.info("=" * 80)
        self.logger.info(f"AGENT INVOCATION #{self.total_invocations}")
        self.logger.info(f"User Message: {user_message}")
        self.logger.info("=" * 80)

    def after_agent(self, callback_context: CallbackContext) -> None:
        """Called after agent completes processing."""
        agent_response = callback_context.agent_response

        self.logger.info("-" * 80)
        self.logger.info(f"Agent Response: {agent_response}")
        self.logger.info(f"Total tool calls in this turn: {len(callback_context.tool_calls or [])}")
        self.logger.info("-" * 80)

        # Log cumulative metrics
        self._log_metrics_summary()

    def before_tool(self, callback_context: CallbackContext) -> None:
        """Called before tool execution."""
        tool_name = callback_context.tool_name
        tool_input = callback_context.tool_input

        self.logger.debug(f"  → Calling tool: {tool_name}")
        self.logger.debug(f"    Input: {json.dumps(tool_input, indent=2)}")

        # Store start time for latency tracking
        callback_context.state["tool_start_time"] = datetime.now()

    def after_tool(self, callback_context: CallbackContext) -> None:
        """Called after tool execution."""
        tool_name = callback_context.tool_name
        tool_response = callback_context.tool_response

        # Calculate execution time
        start_time = callback_context.state.get("tool_start_time")
        if start_time:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.tool_timings[tool_name].append(execution_time)
        else:
            execution_time = 0.0

        # Track tool invocation
        self.tool_counts[tool_name] += 1

        self.logger.debug(f"  ← Tool completed: {tool_name} ({execution_time:.3f}s)")

        # Parse response for data generation tracking
        if tool_name == "generate_perfect_data":
            self._track_data_generation(tool_response)

        self.logger.debug(f"    Response: {json.dumps(tool_response, indent=2)}")

    def _track_data_generation(self, response: dict[str, Any]) -> None:
        """Track metrics from data generation tool responses."""
        if response.get("status") == "success":
            self.data_stats["successful_generations"] += 1

            # Track table-specific stats
            table_name = response.get("table_name")
            if table_name:
                self.data_stats["tables_generated"][table_name] += 1

            # Track total rows
            rows = response.get("rows_generated", 0)
            self.data_stats["total_rows"] += rows

            # Track logic dates
            logic_date = response.get("logic_date")
            if logic_date:
                self.data_stats["logic_dates"].add(logic_date)

            self.logger.info(f"  ✓ Data generated: {table_name} | {rows} rows | {logic_date}")
        else:
            self.data_stats["failed_generations"] += 1
            error_msg = response.get("error_message", "Unknown error")
            self.tool_errors[response.get("table_name", "unknown")] += 1
            self.logger.warning(f"  ✗ Data generation failed: {error_msg}")

    def _log_metrics_summary(self) -> None:
        """Log cumulative metrics summary."""
        session_duration = (datetime.now() - self.session_start_time).total_seconds()

        self.logger.info("")
        self.logger.info("📊 METRICS SUMMARY")
        self.logger.info(f"  Session Duration: {session_duration:.1f}s")
        self.logger.info(f"  Total Invocations: {self.total_invocations}")

        if self.tool_counts:
            self.logger.info("  Tool Calls:")
            for tool_name, count in self.tool_counts.items():
                avg_time = (
                    sum(self.tool_timings[tool_name]) / len(self.tool_timings[tool_name])
                    if self.tool_timings[tool_name]
                    else 0
                )
                self.logger.info(f"    - {tool_name}: {count} calls (avg: {avg_time:.3f}s)")

        # Data generation stats
        if self.data_stats["successful_generations"] > 0:
            self.logger.info("  Data Generation:")
            self.logger.info(f"    - Successful: {self.data_stats['successful_generations']}")
            self.logger.info(f"    - Failed: {self.data_stats['failed_generations']}")
            self.logger.info(f"    - Total Rows: {self.data_stats['total_rows']:,}")
            self.logger.info(f"    - Unique Dates: {len(self.data_stats['logic_dates'])}")

            if self.data_stats["tables_generated"]:
                self.logger.info("    - Tables:")
                for table, count in self.data_stats["tables_generated"].items():
                    self.logger.info(f"      • {table}: {count} files")

        if self.tool_errors:
            self.logger.info("  Errors:")
            for table, count in self.tool_errors.items():
                self.logger.info(f"    - {table}: {count} errors")

        self.logger.info("")

    def get_metrics(self) -> dict[str, Any]:
        """
        Get current metrics as a dictionary.

        Returns:
            Dictionary containing all tracked metrics
        """
        return {
            "agent_name": self.agent_name,
            "session_duration_seconds": (datetime.now() - self.session_start_time).total_seconds(),
            "total_invocations": self.total_invocations,
            "tool_counts": dict(self.tool_counts),
            "tool_errors": dict(self.tool_errors),
            "tool_avg_latency": {
                tool: sum(times) / len(times) if times else 0
                for tool, times in self.tool_timings.items()
            },
            "data_generation": {
                "successful": self.data_stats["successful_generations"],
                "failed": self.data_stats["failed_generations"],
                "total_rows": self.data_stats["total_rows"],
                "unique_dates": len(self.data_stats["logic_dates"]),
                "tables": dict(self.data_stats["tables_generated"]),
            },
        }

    def save_metrics(self, filepath: str | Path | None = None) -> Path:
        """
        Save metrics to a JSON file.

        Args:
            filepath: Optional custom filepath. If None, uses default location.

        Returns:
            Path to the saved metrics file
        """
        if filepath is None:
            filepath = (
                settings.log_dir / f"{self.agent_name}_metrics_{datetime.now():%Y%m%d_%H%M%S}.json"
            )

        filepath = Path(filepath)
        metrics = self.get_metrics()

        # Convert set to list for JSON serialization
        metrics["data_generation"]["logic_dates"] = list(self.data_stats["logic_dates"])

        with open(filepath, "w") as f:
            json.dump(metrics, f, indent=2)

        self.logger.info(f"Metrics saved to: {filepath}")
        return filepath
