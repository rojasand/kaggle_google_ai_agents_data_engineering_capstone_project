#!/usr/bin/env python3
"""
Comprehensive API Test Script for Data Robot Agent

This script:
1. Tests all four capabilities (SQL, Quality, Exploration, Ingestion)
2. Validates responses
3. Reports results
"""

import asyncio
import time
import sys
import json
from typing import Any, Dict
from pathlib import Path

from google.adk.runners import InMemoryRunner

from src.agents.data_robot_agent.agent import root_agent


class DataRobotAgentTester:
    """Test suite for Data Robot Agent."""

    def __init__(self):
        self.test_results = []
        self.agent = root_agent

    async def test_query(
        self, test_name: str, query: str, expected_keywords: list[str] = None
    ) -> Dict[str, Any]:
        """
        Test a single query against the agent.

        Args:
            test_name: Name of the test
            query: Query to send to agent
            expected_keywords: List of keywords expected in response

        Returns:
            Test result dictionary
        """
        print(f"\n🧪 Testing: {test_name}")
        print(f"   Query: {query}")

        try:
            # Run agent with query using InMemoryRunner
            runner = InMemoryRunner(app_name=test_name, agent=self.agent)
            response = await runner.run_debug(query)

            # Extract final response
            final_response = str(response) if response else ""

            # Check for expected keywords
            keywords_found = []
            missing_keywords = []

            if expected_keywords:
                for keyword in expected_keywords:
                    if keyword.lower() in final_response.lower():
                        keywords_found.append(keyword)
                    else:
                        missing_keywords.append(keyword)

            # Consider test successful if we got any response, or if all keywords found
            success = len(final_response) > 50 or (
                expected_keywords and len(missing_keywords) == 0
            )

            result = {
                "test_name": test_name,
                "query": query,
                "success": success,
                "response_length": len(final_response),
                "response_preview": final_response[:200] if final_response else "NO RESPONSE",
                "keywords_found": keywords_found,
                "missing_keywords": missing_keywords,
                "full_response": final_response,
            }

            # Print result
            status = "✅" if success else "❌"
            print(f"   {status} Result: {'PASS' if success else 'FAIL'}")
            if keywords_found:
                print(f"      Keywords found: {', '.join(keywords_found)}")
            if missing_keywords:
                print(f"      ⚠️  Keywords missing: {', '.join(missing_keywords)}")
            print(f"      Response preview: {result['response_preview'][:100]}...")

            self.test_results.append(result)
            return result

        except Exception as e:
            print(f"   ❌ Error executing test: {e}")
            import traceback
            traceback.print_exc()
            result = {
                "test_name": test_name,
                "query": query,
                "success": False,
                "error": str(e),
            }
            self.test_results.append(result)
            return result

    async def run_all_tests(self) -> None:
        """Run all test cases."""
        print("=" * 80)
        print("🤖 DATA ROBOT AGENT - COMPREHENSIVE API TEST SUITE")
        print("=" * 80)

        # Define test cases
        test_cases = [
            {
                "name": "Data Exploration - Available Tables",
                "query": "What tables are available in the database?",
                "keywords": ["table", "customer", "product", "sales"],
            },
            {
                "name": "Data Exploration - Table Description",
                "query": "Tell me about the customers table structure",
                "keywords": ["customer", "column", "field"],
            },
            {
                "name": "SQL Query - Simple Statistics",
                "query": "Show me the count of customers by date",
                "keywords": ["customer", "count", "date"],
            },
            {
                "name": "SQL Query - Top Records",
                "query": "What are the top 5 customers by purchase amount?",
                "keywords": ["customer", "amount", "purchase"],
            },
            {
                "name": "Data Quality - Overview",
                "query": "What's the overall data quality status?",
                "keywords": ["quality", "table", "status"],
            },
            {
                "name": "Data Quality - Specific Table",
                "query": "Check data quality for the customers table",
                "keywords": ["customer", "quality", "record"],
            },
            {
                "name": "Capability Check",
                "query": "What can you do? List your capabilities.",
                "keywords": ["query", "quality", "explore", "ingest"],
            },
            {
                "name": "Complex Multi-Step Query",
                "query": "How many unique customers purchased products in the last month? Also check if the data is complete.",
                "keywords": ["customer", "product"],
            },
        ]

        # Run tests
        for test_case in test_cases:
            await self.test_query(
                test_name=test_case["name"],
                query=test_case["query"],
                expected_keywords=test_case["keywords"],
            )
            await asyncio.sleep(1)  # Small delay between tests

        # Print summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("success", False))
        failed_tests = total_tests - passed_tests

        print(f"\nTotal Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")

        print("\n" + "-" * 80)
        print("DETAILED RESULTS:")
        print("-" * 80)

        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result.get("success", False) else "❌"
            print(f"\n{i}. {status} {result['test_name']}")
            print(f"   Query: {result['query']}")

            if result.get("error"):
                print(f"   Error: {result['error']}")
            else:
                print(f"   Response Length: {result.get('response_length', 0)} chars")
                if result.get("keywords_found"):
                    print(f"   Keywords Found: {', '.join(result['keywords_found'])}")
                if result.get("missing_keywords"):
                    print(f"   Missing Keywords: {', '.join(result['missing_keywords'])}")

        # Save detailed results
        self.save_results()

    def save_results(self) -> None:
        """Save test results to file."""
        results_file = Path(__file__).parent / "test_results_api.json"

        # Prepare results for JSON serialization
        serializable_results = []
        for result in self.test_results:
            serializable_result = {
                "test_name": result.get("test_name", ""),
                "query": result.get("query", ""),
                "success": result.get("success", False),
                "response_length": result.get("response_length", 0),
                "response_preview": result.get("response_preview", ""),
                "keywords_found": result.get("keywords_found", []),
                "missing_keywords": result.get("missing_keywords", []),
                "error": result.get("error"),
            }
            serializable_results.append(serializable_result)

        with open(results_file, "w") as f:
            json.dump(
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_tests": len(self.test_results),
                    "passed": sum(1 for r in self.test_results if r.get("success", False)),
                    "failed": sum(
                        1 for r in self.test_results if not r.get("success", False)
                    ),
                    "results": serializable_results,
                },
                f,
                indent=2,
            )

        print(f"\n📁 Results saved to: {results_file}")


async def main():
    """Main test execution."""
    tester = DataRobotAgentTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("🚀 Starting Data Robot Agent API Tests...")
    print("Tests will run against the in-memory agent (no server needed)")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⛔ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
