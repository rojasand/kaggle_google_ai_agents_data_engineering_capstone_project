"""SQL query execution tools with safety checks and history tracking."""

import re
import uuid
from datetime import date

from google.adk.tools import ToolContext

from src.config import settings
from src.database.connection import get_db_connection
from src.tools.exploration_tools import serialize_value

# Default row limit for queries
DEFAULT_ROW_LIMIT = settings.default_row_limit


def execute_select_query(
    query_text: str,
    session_id: str | None = None,
    tool_context: ToolContext | None = None,
    requested_limit: int | None = None,
) -> dict:
    """
    Execute a SELECT SQL query safely and track it in query_history.

    This tool executes only SELECT queries (read-only) for safety.
    All queries are logged to the query_history table for audit purposes.

    For queries returning many rows, this tool will automatically:
    1. Count total rows before execution
    2. If rows > DEFAULT_ROW_LIMIT, pause and ask user for confirmation
    3. Resume with user's choice (all, specific limit, or default limit)

    Args:
        query_text (str): The SQL SELECT query to execute
        session_id (str | None): Optional session identifier for tracking.
                                  If None, generates a new UUID.
        tool_context (ToolContext | None): ADK tool context for LRO pause/resume.
                                            Required for row limit confirmation.
        requested_limit (int | None): User-specified row limit from resume.
                                       None = use DEFAULT_ROW_LIMIT,
                                       0 = no limit (return all rows)

    Returns:
        dict: Execution result dictionary
            - status (str): "success" or "error"
            - query_text (str): The executed query
            - session_id (str): Session identifier
            - rows_returned (int): Number of rows in result (success only)
            - results (list): List of row dictionaries (success only)
            - columns (list): List of column names (success only)
            - error_message (str): Error details (error only)
            - message (str): Helpful description

    Safety:
        - Only SELECT queries allowed
        - Blocks: DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, TRUNCATE
        - Query history tracked for all attempts

    Example:
        >>> result = execute_select_query("SELECT COUNT(*) as total FROM customers")
        >>> print(result['results'])
        [{'total': 525}]
    """
    # Generate session_id if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    # Normalize query for safety check
    query_normalized = query_text.strip().upper()

    # Safety check: Only allow SELECT queries
    if not query_normalized.startswith("SELECT"):
        error_msg = "Only SELECT queries are allowed for safety reasons"
        _save_query_history(
            session_id=session_id,
            query_text=query_text,
            execution_status="error",
            rows_returned=None,
            error_message=error_msg,
        )
        return {
            "status": "error",
            "query_text": query_text,
            "session_id": session_id,
            "error_message": error_msg,
            "message": "Query rejected: must be a SELECT statement",
        }

    # Check for dangerous keywords (defense in depth)
    dangerous_keywords = [
        "DROP",
        "DELETE",
        "INSERT",
        "UPDATE",
        "ALTER",
        "CREATE",
        "TRUNCATE",
    ]
    for keyword in dangerous_keywords:
        if keyword in query_normalized:
            error_msg = f"Query contains prohibited keyword: {keyword}"
            _save_query_history(
                session_id=session_id,
                query_text=query_text,
                execution_status="error",
                rows_returned=None,
                error_message=error_msg,
            )
            return {
                "status": "error",
                "query_text": query_text,
                "session_id": session_id,
                "error_message": error_msg,
                "message": f"Query rejected: contains {keyword}",
            }

    # Check if query is an aggregation (no row limit needed)
    is_aggregation = _is_aggregation_query(query_text)

    # Determine if we need to apply row limiting
    apply_limit = not is_aggregation and DEFAULT_ROW_LIMIT > 0

    # If tool_context provided and we should apply limits, check row count first
    if tool_context and apply_limit and requested_limit is None:
        # Count total rows to determine if we need confirmation
        try:
            row_count = _count_query_rows(query_text)

            if row_count > DEFAULT_ROW_LIMIT:
                # Pause and ask user for confirmation
                confirmation_msg = (
                    f"This query will return {row_count} rows. "
                    f"Default limit is {DEFAULT_ROW_LIMIT} rows.\n\n"
                    f"How many rows would you like to see?\n"
                    f"• Type 'all' to see all {row_count} rows\n"
                    f"• Type a number (e.g., '50') for a specific limit\n"
                    f"• Type 'no' or press Enter to keep the default ({DEFAULT_ROW_LIMIT} rows)"
                )

                tool_context.request_confirmation(
                    confirmation_msg,
                    confirmation_data={
                        "query_text": query_text,
                        "session_id": session_id,
                        "row_count": row_count,
                        "default_limit": DEFAULT_ROW_LIMIT,
                    },
                )

                # Execution will resume when user responds
                return {
                    "status": "pending_confirmation",
                    "query_text": query_text,
                    "session_id": session_id,
                    "row_count": row_count,
                    "message": f"Query will return {row_count} rows. Awaiting user confirmation.",
                }
        except Exception as e:
            # If count fails, continue without confirmation
            print(f"Warning: Could not count rows: {e}")

    # Determine the final limit to apply
    final_limit = None
    if apply_limit:
        if requested_limit is not None:
            # User specified a limit during resume (0 = no limit)
            final_limit = requested_limit if requested_limit > 0 else None
        else:
            # Apply default limit
            final_limit = DEFAULT_ROW_LIMIT

    # Add LIMIT clause if needed
    final_query = query_text
    if final_limit and not _has_limit_clause(query_text):
        final_query = f"{query_text.rstrip().rstrip(';')} LIMIT {final_limit}"

    # Execute the query
    try:
        with get_db_connection() as conn:
            result = conn.execute(final_query).fetchall()

            # Get column names
            columns = []
            if result:
                # DuckDB returns tuples, get column names from description
                cursor = conn.execute(final_query)
                columns = [desc[0] for desc in cursor.description]

            # Convert rows to list of dicts with serialized values
            rows = []
            for row in result:
                row_dict = {}
                for idx, value in enumerate(row):
                    col_name = columns[idx] if idx < len(columns) else f"col_{idx}"
                    row_dict[col_name] = serialize_value(value)
                rows.append(row_dict)

            rows_returned = len(rows)

            # Save to query history
            _save_query_history(
                session_id=session_id,
                query_text=query_text,
                execution_status="success",
                rows_returned=rows_returned,
                error_message=None,
            )

            return {
                "status": "success",
                "query_text": query_text,
                "executed_query": final_query,
                "session_id": session_id,
                "rows_returned": rows_returned,
                "results": rows,
                "columns": columns,
                "applied_limit": final_limit,
                "is_limited": final_limit is not None and final_query != query_text,
                "message": f"Query executed successfully, returned {rows_returned} rows",
            }

    except Exception as e:
        error_msg = str(e)
        _save_query_history(
            session_id=session_id,
            query_text=query_text,
            execution_status="error",
            rows_returned=None,
            error_message=error_msg,
        )
        return {
            "status": "error",
            "query_text": query_text,
            "session_id": session_id,
            "error_message": error_msg,
            "message": f"Query execution failed: {error_msg}",
        }


def _save_query_history(
    session_id: str,
    query_text: str,
    execution_status: str,
    rows_returned: int | None,
    error_message: str | None,
) -> None:
    """
    Save query execution to history table (internal helper).

    Args:
        session_id: Session identifier
        query_text: The SQL query
        execution_status: 'success' or 'error'
        rows_returned: Number of rows (or None)
        error_message: Error details (or None)
    """
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO query_history (
                    session_id, query_text, execution_status,
                    rows_returned, error_message, creation_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                [
                    session_id,
                    query_text,
                    execution_status,
                    rows_returned,
                    error_message,
                    date.today(),
                ],
            )
            conn.commit()
    except Exception as e:
        # Log but don't raise - history tracking shouldn't block query execution
        print(f"Warning: Failed to save query history: {e}")


def get_query_history(session_id: str | None = None, limit: int = 10) -> dict:
    """
    Retrieve query execution history, optionally filtered by session.

    This tool helps track which queries have been executed, useful for
    auditing and understanding query patterns.

    Args:
        session_id (str | None): Optional session ID to filter by.
                                  If None, returns recent queries from all sessions.
        limit (int): Maximum number of queries to return (default: 10)

    Returns:
        dict: History dictionary
            - status (str): "success" or "error"
            - session_id (str | None): Filter used (if any)
            - queries (list): List of query history records
                - query_id (int): Unique identifier
                - session_id (str): Session identifier
                - query_text (str): The SQL query
                - execution_status (str): "success" or "error"
                - rows_returned (int | None): Number of rows
                - error_message (str | None): Error details
                - creation_timestamp (str): When executed
            - total_queries (int): Number of queries returned
            - message (str): Helpful description

    Example:
        >>> result = get_query_history(limit=5)
        >>> print(result['queries'])
        [{'query_id': 1, 'query_text': 'SELECT ...', ...}, ...]
    """
    try:
        with get_db_connection() as conn:
            if session_id:
                result = conn.execute(
                    """
                    SELECT
                        query_id, session_id, query_text, execution_status,
                        rows_returned, error_message, creation_timestamp
                    FROM query_history
                    WHERE session_id = ?
                    ORDER BY query_id DESC
                    LIMIT ?
                """,
                    [session_id, limit],
                ).fetchall()
            else:
                result = conn.execute(
                    """
                    SELECT
                        query_id, session_id, query_text, execution_status,
                        rows_returned, error_message, creation_timestamp
                    FROM query_history
                    ORDER BY query_id DESC
                    LIMIT ?
                """,
                    [limit],
                ).fetchall()

            queries = []
            for row in result:
                query = {
                    "query_id": row[0],
                    "session_id": row[1],
                    "query_text": row[2],
                    "execution_status": row[3],
                    "rows_returned": row[4],
                    "error_message": row[5],
                    "creation_timestamp": serialize_value(row[6]),
                }
                queries.append(query)

            if not queries:
                if session_id:
                    msg = f"No query history found for session: {session_id}"
                else:
                    msg = "No query history found in database"

                return {
                    "status": "success",
                    "session_id": session_id,
                    "queries": [],
                    "total_queries": 0,
                    "message": msg,
                }

            if session_id:
                msg = f"Found {len(queries)} queries for session: {session_id}"
            else:
                msg = f"Found {len(queries)} recent queries"

            return {
                "status": "success",
                "session_id": session_id,
                "queries": queries,
                "total_queries": len(queries),
                "message": msg,
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to retrieve query history: {str(e)}",
            "message": "An error occurred while retrieving query history",
        }


def _is_aggregation_query(query_text: str) -> bool:
    """
    Check if a query is an aggregation query (no row limit needed).

    Aggregation indicators:
    - GROUP BY clause
    - Aggregate functions: COUNT, SUM, AVG, MAX, MIN, etc.

    Args:
        query_text: SQL query to analyze

    Returns:
        bool: True if query is an aggregation
    """
    query_upper = query_text.upper()

    # Check for GROUP BY
    if re.search(r"\bGROUP\s+BY\b", query_upper):
        return True

    # Check for aggregate functions
    agg_functions = [
        r"\bCOUNT\s*\(",
        r"\bSUM\s*\(",
        r"\bAVG\s*\(",
        r"\bMAX\s*\(",
        r"\bMIN\s*\(",
        r"\bSTDDEV\s*\(",
        r"\bVARIANCE\s*\(",
    ]

    for pattern in agg_functions:
        if re.search(pattern, query_upper):
            return True

    return False


def _has_limit_clause(query_text: str) -> bool:
    """
    Check if query already has a LIMIT clause.

    Args:
        query_text: SQL query to check

    Returns:
        bool: True if LIMIT clause exists
    """
    return bool(re.search(r"\bLIMIT\s+\d+", query_text, re.IGNORECASE))


def _count_query_rows(query_text: str) -> int:
    """
    Count total rows that would be returned by a query.

    Wraps the query in SELECT COUNT(*) FROM (query) to get row count.

    Args:
        query_text: SQL query to count rows for

    Returns:
        int: Total number of rows

    Raises:
        Exception: If count query fails
    """
    # Remove any trailing semicolon
    clean_query = query_text.rstrip().rstrip(";")

    # Wrap in count query
    count_query = f"SELECT COUNT(*) as row_count FROM ({clean_query}) AS subquery"

    with get_db_connection() as conn:
        result = conn.execute(count_query).fetchone()
        return result[0] if result else 0
