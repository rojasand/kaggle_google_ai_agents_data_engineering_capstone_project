"""SQL query execution tools with safety checks and history tracking."""

import uuid
from datetime import date

from src.database.connection import get_db_connection
from src.tools.exploration_tools import serialize_value


def execute_select_query(query_text: str, session_id: str | None = None) -> dict:
    """
    Execute a SELECT SQL query safely and track it in query_history.

    This tool executes only SELECT queries (read-only) for safety.
    All queries are logged to the query_history table for audit purposes.

    Args:
        query_text (str): The SQL SELECT query to execute
        session_id (str | None): Optional session identifier for tracking.
                                  If None, generates a new UUID.

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

    # Execute the query
    try:
        with get_db_connection() as conn:
            result = conn.execute(query_text).fetchall()

            # Get column names
            columns = []
            if result:
                # DuckDB returns tuples, get column names from description
                cursor = conn.execute(query_text)
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
                "session_id": session_id,
                "rows_returned": rows_returned,
                "results": rows,
                "columns": columns,
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
