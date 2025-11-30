"""Test observability features with ADK API server."""

import asyncio
import json
import time

import httpx
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

from src.agents.data_source_agent.agent_with_observability import (
    metrics_plugin,
    root_agent,
)
from src.config import settings


async def test_observability_with_runner():
    """Test observability with Runner (local execution)."""
    print("\n" + "=" * 80)
    print("TEST 1: Local Observability with Runner")
    print("=" * 80 + "\n")

    # Create session service and runner with metrics plugin
    session_service = InMemorySessionService()

    runner = Runner(
        app_name="test_observability",
        agent=root_agent,
        session_service=session_service,
        plugins=[metrics_plugin],
    )

    print("📝 Running test scenarios...\n")

    # Test scenario 1: Successful data generation
    test_cases = [
        "Generate customers data for 2025-01-15",
        "I need products data for 2025-02-20",
        "Create sales_transactions for 2025-03-01",
        "Generate data for invalid_table on 2025-01-01",  # Should fail gracefully
    ]

    for i, user_message in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}/{len(test_cases)} ---")
        print(f"User: {user_message}")

        # Run the agent using run_debug
        events = await runner.run_debug(user_messages=user_message, quiet=True)

        # Display response
        for event in events:
            if hasattr(event, "content") and event.content:
                content_str = str(event.content)
                if hasattr(event.content, "text"):
                    content_str = event.content.text
                print(f"Agent: {content_str[:200]}...")
                break

        await asyncio.sleep(1)  # Small delay between requests

    print("\n" + "=" * 80)
    print("📊 FINAL METRICS SUMMARY")
    print("=" * 80)

    metrics = metrics_plugin.get_metrics()
    print(json.dumps(metrics, indent=2))

    # Save metrics
    metrics_file = metrics_plugin.save_metrics()
    print(f"\n✅ Metrics saved to: {metrics_file}")

    print("\n✅ Test completed! Check the log file for detailed observability data")
    print("   Log file contains timestamped events, tool calls, and performance metrics")

    return metrics


async def test_observability_with_api_server():
    """Test observability by calling the ADK API server."""
    print("\n" + "=" * 80)
    print("TEST 2: Remote Observability with API Server")
    print("=" * 80 + "\n")

    # API server base URL
    base_url = "http://localhost:8000"

    # Test if server is running
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code != 200:
                print("❌ ADK API Server is not running!")
                print("   Start it with: make run-adk-api")
                return None
        except httpx.ConnectError:
            print("❌ ADK API Server is not running!")
            print("   Start it with: make run-adk-api")
            return None

    print("✅ API Server is running\n")

    # Create a session
    session_data = {
        "app_name": "data_source_agent",
        "user_id": "test_user_api",
        "session_id": f"test_session_{int(time.time())}",
    }

    print(f"📝 Creating session: {session_data['session_id']}\n")

    # Test scenarios
    test_messages = [
        "Generate customers data for 2025-11-28",
        "Create products data for 2025-11-28",
        "Generate sales_transactions for 2025-11-28",
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- API Test {i}/{len(test_messages)} ---")
            print(f"User: {message}")

            # Send message to agent
            payload = {
                "app_name": session_data["app_name"],
                "user_id": session_data["user_id"],
                "session_id": session_data["session_id"],
                "user_message": message,
            }

            response = await client.post(
                f"{base_url}/run",
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                # Extract agent response from events
                for event in result.get("events", []):
                    if event.get("type") == "agent_response":
                        agent_message = event.get("content", "")
                        print(f"Agent: {agent_message[:200]}...")
            else:
                print(f"❌ API Error: {response.status_code}")
                print(response.text)

            await asyncio.sleep(1)

    print("\n✅ API Server test completed!")
    print("\n📊 Check the server logs for detailed metrics")

    return session_data


async def main_async():
    """Run all observability tests asynchronously."""
    print("\n" + "=" * 80)
    print("OBSERVABILITY TEST SUITE")
    print("Testing Data Source Agent with Metrics Tracking")
    print("=" * 80)

    # Ensure directories exist
    settings.ensure_directories()

    # Test 1: Local execution with Runner
    print("\n🧪 Starting Test 1: Local Execution")
    metrics = await test_observability_with_runner()

    # Test 2: API Server (if available)
    print("\n\n🧪 Starting Test 2: API Server")
    print("Note: This test requires the ADK API server to be running")
    print("      Start it with: make run-adk-api")

    try:
        await test_observability_with_api_server()
    except Exception as e:
        print(f"\n⚠️  API Server test skipped: {e}")

    print("\n" + "=" * 80)
    print("🎉 OBSERVABILITY TESTS COMPLETED")
    print("=" * 80)
    print(f"\n📁 Check logs in: {settings.log_dir}")
    print(f"📊 Check metrics in: {settings.log_dir}")

    return metrics


def main():
    """Synchronous wrapper for main_async."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
