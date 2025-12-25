"""Low-level helper to execute raw SQL against Django's database.

This module exposes :func:`execute_sql` which runs a parameterized SQL
query using Django's database connection and returns column names and
rows. It is intended for one-off queries where ORM abstractions are
insufficient or when reading complex reports from the database.

The helper uses Django's connection cursor context manager to ensure
resources are cleaned up correctly. Results are fetched into memory so
avoid using it for very large result sets.
"""

from typing import Any

from django.db import connection


def execute_sql(
    sql: str, params: dict[str, Any] | None = None
) -> tuple[list[str], list[tuple[Any, ...]]]:
    """Execute a SQL statement and return column names and rows.

    Args:
        sql (str): SQL statement possibly containing named placeholders
            (``%(name)s``) for database binding.
        params (dict[str, Any] | None): Optional mapping of parameters to
            bind to the query.

    Returns:
        Tuple[List[str], List[Tuple[Any, ...]]]: A tuple where the first
        element is the list of column names (empty list if the statement
        returned no rows) and the second element is a list of row tuples.

    Raises:
        django.db.Error: Propagates underlying database errors raised by
            Django's database backend.
    """
    with connection.cursor() as cursor:
        cursor.execute(sql=sql, params=params)
        rows = cursor.fetchall()
        column_names = (
            [col[0] for col in cursor.description] if cursor.description else []
        )

    return column_names, rows
