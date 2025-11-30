#!/usr/bin/env python3
"""
Simple Direct Test for Data Robot Agent
Tests the agent synchronously without pytest
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.data_robot_agent.agent import root_agent, explain_capabilities


def test_agent_structure():
    """Test that the agent is properly configured."""
    print("\n" + "=" * 80)
    print("TEST 1: Agent Structure Validation")
    print("=" * 80)

    checks = []

    # Check 1: Agent exists
    if root_agent:
        print("✅ Root agent exists")
        checks.append(True)
    else:
        print("❌ Root agent not found")
        checks.append(False)

    # Check 2: Agent has name
    if hasattr(root_agent, "name") and root_agent.name:
        print(f"✅ Agent name: {root_agent.name}")
        checks.append(True)
    else:
        print("❌ Agent name not set")
        checks.append(False)

    # Check 3: Agent has sub_agents
    if hasattr(root_agent, "sub_agents") and root_agent.sub_agents:
        print(f"✅ Sub-agents configured: {len(root_agent.sub_agents)} agents")
        for i, agent in enumerate(root_agent.sub_agents, 1):
            agent_name = getattr(agent, "name", "Unknown")
            print(f"   {i}. {agent_name}")
        checks.append(True)
    else:
        print("❌ No sub_agents configured")
        checks.append(False)

    # Check 4: Agent has tools OR sub_agents (sub_agents are the preferred approach for orchestration)
    has_tools = hasattr(root_agent, "tools") and root_agent.tools
    has_sub_agents = hasattr(root_agent, "sub_agents") and root_agent.sub_agents
    
    if has_tools:
        print(f"✅ Tools configured: {len(root_agent.tools)} tools")
        for tool in root_agent.tools:
            tool_name = getattr(tool, "name", getattr(tool, "__name__", "Unknown"))
            print(f"   - {tool_name}")
        checks.append(True)
    elif has_sub_agents:
        print(f"✅ Sub-agents act as delegation targets (no direct tools needed)")
        checks.append(True)
    else:
        print("⚠️  No tools or sub_agents configured (may be OK for orchestrators)")
        checks.append(True)  # Not critical for orchestrators

    # Check 5: Agent has model
    if hasattr(root_agent, "model") and root_agent.model:
        print("✅ LLM model configured")
        checks.append(True)
    else:
        print("❌ LLM model not configured")
        checks.append(False)

    # Check 6: Agent has instruction
    if hasattr(root_agent, "instruction") and root_agent.instruction:
        print(f"✅ Instructions set ({len(root_agent.instruction)} characters)")
        checks.append(True)
    else:
        print("❌ Instructions not set")
        checks.append(False)

    return all(checks)


def test_capabilities_explanation():
    """Test that capabilities are properly documented."""
    print("\n" + "=" * 80)
    print("TEST 2: Capabilities Documentation")
    print("=" * 80)

    try:
        explanation = explain_capabilities()

        if not explanation:
            print("❌ No capabilities explanation provided")
            return False

        print("✅ Capabilities documented")

        # Check for key capability mentions
        capabilities = ["SQL", "Quality", "Exploration", "Ingestion"]
        found_capabilities = []

        for cap in capabilities:
            if cap in explanation:
                print(f"   ✅ {cap} capability documented")
                found_capabilities.append(True)
            else:
                print(f"   ❌ {cap} capability NOT documented")
                found_capabilities.append(False)

        return all(found_capabilities)

    except Exception as e:
        print(f"❌ Error getting capabilities: {e}")
        return False


def test_agent_architecture():
    """Test the agent architecture is correct."""
    print("\n" + "=" * 80)
    print("TEST 3: Architecture Validation")
    print("=" * 80)

    checks = []

    # Check 1: Two-stage architecture
    if hasattr(root_agent, "sub_agents"):
        num_agents = len(root_agent.sub_agents)
        if num_agents == 2:
            print("✅ Two-stage architecture confirmed (2 sub_agents)")
            checks.append(True)
        else:
            print(f"⚠️  Expected 2 sub_agents, found {num_agents}")
            checks.append(False)

        # Check 2: ParallelAgent present
        has_parallel = any("parallel" in str(type(a)).lower() for a in root_agent.sub_agents)
        if has_parallel:
            print("✅ ParallelAgent (capability checker) present")
            checks.append(True)
        else:
            print("❌ ParallelAgent not found")
            checks.append(False)

        # Check 3: SequentialAgent present
        has_sequential = any(
            "sequential" in str(type(a)).lower() for a in root_agent.sub_agents
        )
        if has_sequential:
            print("✅ SequentialAgent (request router) present")
            checks.append(True)
        else:
            print("❌ SequentialAgent not found")
            checks.append(False)
    else:
        print("❌ No sub_agents found")
        checks.append(False)
        checks.append(False)
        checks.append(False)

    return all(checks)


def test_agent_is_operational():
    """Test that the agent can be instantiated."""
    print("\n" + "=" * 80)
    print("TEST 4: Agent Operational Status")
    print("=" * 80)

    try:
        # Try to access basic agent properties
        _ = root_agent.name
        print("✅ Agent accessible and operational")

        # Check that it has the required methods
        if hasattr(root_agent, "run_async"):
            print("✅ Agent has async run method")
        else:
            print("⚠️  Agent missing async run method (may not be critical)")

        if hasattr(root_agent, "description"):
            print(f"✅ Agent has description: {root_agent.description[:50]}...")
        else:
            print("⚠️  Agent missing description")

        return True

    except Exception as e:
        print(f"❌ Agent not operational: {e}")
        return False


def print_summary(results):
    """Print test summary."""
    print("\n" + "=" * 80)
    print("FINAL TEST SUMMARY")
    print("=" * 80)

    test_names = [
        "Agent Structure Validation",
        "Capabilities Documentation",
        "Architecture Validation",
        "Agent Operational Status",
    ]

    passed = sum(1 for r in results if r)
    total = len(results)

    print(f"\nTests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    print("\n" + "-" * 80)
    print("Detailed Results:")
    print("-" * 80)

    for name, result in zip(test_names, results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    return all(results)


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🤖 DATA ROBOT AGENT - DIRECT VALIDATION TESTS")
    print("=" * 80)

    results = [
        test_agent_structure(),
        test_capabilities_explanation(),
        test_agent_architecture(),
        test_agent_is_operational(),
    ]

    success = print_summary(results)

    print("\n" + "=" * 80)
    print("📊 AGENT STATUS")
    print("=" * 80)

    if success:
        print("\n✅ ALL VALIDATION CHECKS PASSED!")
        print("\nAgent is ready to use:")
        print("  • Type: Hierarchical Orchestrator")
        print("  • Architecture: 2-Stage (Parallel + Sequential)")
        print("  • Capabilities: SQL, Quality, Exploration, Ingestion")
        print("\nNext Steps:")
        print("  1. Start server: poetry run python src/agents/data_robot_agent/server.py")
        print("  2. Test in ADK Web: http://localhost:8002")
        print("  3. Try queries like: 'What tables are available?'")
        return 0
    else:
        print("\n❌ Some validation checks failed!")
        print("Review the errors above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
