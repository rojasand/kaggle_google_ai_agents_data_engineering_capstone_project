"""Workflow orchestration for SQL Agent with Long-Running Operations.

This module handles the pause/resume workflow when queries return
more than the default row limit (10 rows).
"""

import re
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def check_for_approval(events):
    """Check if events contain an approval request.

    Args:
        events: List of events from agent execution

    Returns:
        dict with approval details or None if no approval needed
            - approval_id: ID of the confirmation request
            - invocation_id: ID to resume execution
            - hint: The hint message with total row count
    """
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if (
                    part.function_call
                    and part.function_call.name == "adk_request_confirmation"
                ):
                    # Extract hint from function call arguments
                    hint = None
                    if hasattr(part.function_call, "args") and part.function_call.args:
                        hint = part.function_call.args.get("hint", "")

                    return {
                        "approval_id": part.function_call.id,
                        "invocation_id": event.invocation_id,
                        "hint": hint,
                    }
    return None


def print_agent_response(events):
    """Print agent's text responses from events.

    Args:
        events: List of events from agent execution
    """
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"\n{part.text}")


def create_approval_response(approval_info, confirmed):
    """Create approval response message with user's confirmation.

    Args:
        approval_info: Dictionary with approval_id and invocation_id
        confirmed: Boolean - True to see all rows, False to keep first 10

    Returns:
        Content object with function response
    """
    confirmation_response = types.FunctionResponse(
        id=approval_info["approval_id"],
        name="adk_request_confirmation",
        response={"confirmed": confirmed},
    )
    return types.Content(
        role="user", parts=[types.Part(function_response=confirmation_response)]
    )


def parse_user_confirmation(user_input: str) -> bool:
    """Parse user input for confirmation.

    Args:
        user_input: User's response (e.g., "yes", "y", "no", "n")

    Returns:
        bool: True to see all rows, False to keep first 10
    """
    user_input = user_input.strip().lower()

    # Check for affirmative
    if user_input in ["yes", "y", "all", "a", "1", "true"]:
        return True

    # Check for negative
    if user_input in ["no", "n", "none", "0", "false"]:
        return False

    # Default to yes if unclear
    print(f"⚠️  Unclear input '{user_input}', defaulting to 'yes' (show all)")
    return True


async def run_sql_workflow(
    sql_app,
    query: str,
    session_service: InMemorySessionService | None = None,
    user_id: str = "test_user",
    auto_input: str | None = None,
):
    """Run a SQL workflow with automatic row limit handling.

    This workflow:
    1. Executes the SQL query
    2. If results > 10 rows, pauses and asks user for confirmation
    3. Resumes with user's requested limit (all/number/none)

    Args:
        sql_app: The SQL App with resumability enabled
        query: Natural language query or SQL query
        session_service: Session service (creates new if None)
        user_id: User identifier for session
        auto_input: For testing - automatically provide this input instead of prompting
                   (e.g., "all", "50", "no")

    Returns:
        Final agent response
    """
    # Create session service if not provided
    if session_service is None:
        session_service = InMemorySessionService()

    # Create runner
    runner = Runner(app=sql_app, session_service=session_service)

    print(f"\n{'='*70}")
    print(f"🔍 Query: {query}")
    print(f"{'='*70}")

    # Generate unique session ID
    session_id = f"sql_{uuid.uuid4().hex[:8]}"

    # Create session
    await session_service.create_session(
        app_name=sql_app.name, user_id=user_id, session_id=session_id
    )

    # Prepare query content
    query_content = types.Content(role="user", parts=[types.Part(text=query)])
    events = []

    # STEP 1: Send initial request to the agent
    print("\n⏳ Executing query...")
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=query_content
    ):
        events.append(event)

    # STEP 2: Check if agent paused for approval
    approval_info = check_for_approval(events)

    if approval_info:
        # STEP 3: Agent paused - query returned > 10 rows
        print("\n" + "=" * 70)
        print("⏸️  Query returned more than 10 rows")

        # Extract total rows from hint
        hint = approval_info.get("hint", "")
        match = re.search(r"returns (\d+) rows", hint)
        total_rows = int(match.group(1)) if match else "many"

        print(f"📊 Total rows available: {total_rows}")
        print("✅ Showing first 10 rows")

        # Show initial results
        print_agent_response(events)

        # Get user decision
        print("\n" + "=" * 70)
        if auto_input is not None:
            # Testing mode - use provided input
            user_input = auto_input
            print(f"🤖 Auto-input: {user_input}")
        else:
            # Interactive mode - ask user
            print("Would you like to see all rows?")
            print("  • Enter 'yes' or 'y' to see all rows")
            print("  • Enter 'no' or 'n' to keep first 10 only")
            user_input = input("\n👤 Your choice: ").strip()

        user_confirmed = parse_user_confirmation(user_input)

        if not user_confirmed:
            print("\n✅ Keeping first 10 rows only")
            print("=" * 70 + "\n")
            return events

        print(f"\n🔄 Fetching all {total_rows} rows...")
        print("=" * 70)

        # STEP 4: Resume with user's confirmation
        approval_response = create_approval_response(approval_info, user_confirmed)
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=approval_response,
            invocation_id=approval_info["invocation_id"],
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"\n{part.text}")

        print("\n" + "=" * 70 + "\n")
    else:
        # No approval needed - query completed immediately
        print("\n✅ Query completed (≤10 rows)")
        print_agent_response(events)
        print("\n" + "=" * 70 + "\n")

    return events
