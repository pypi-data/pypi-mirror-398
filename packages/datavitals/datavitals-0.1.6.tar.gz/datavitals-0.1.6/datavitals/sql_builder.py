from __future__ import annotations

from typing import List, Union, Optional
import re


class SQLBuilderError(Exception):
    """Raised when SQL query construction fails."""


# Allow only safe SQL identifiers (table / column names)
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(name: str, kind: str) -> None:
    if not isinstance(name, str) or not name.strip():
        raise SQLBuilderError(f"{kind} name must be a non-empty string")

    if not _IDENTIFIER_PATTERN.match(name):
        raise SQLBuilderError(
            f"Invalid {kind} name '{name}'. "
            "Only letters, numbers and underscores allowed."
        )


def select_query(
    table: str,
    columns: Union[List[str], str] = "*",
    where: Optional[str] = None,
) -> str:
    """
    Enterprise-grade SELECT SQL query builder.

    Parameters
    ----------
    table : str
        Table name
    columns : list[str] | str
        Columns to select or '*'
    where : str, optional
        WHERE clause (without 'WHERE')

    Returns
    -------
    str
        Safe SQL SELECT query

    Raises
    ------
    SQLBuilderError
        If query construction fails
    """

    try:
        # ---------- Validate table ----------
        _validate_identifier(table, "Table")

        # ---------- Validate columns ----------
        if isinstance(columns, list):
            if not columns:
                raise SQLBuilderError("Columns list cannot be empty")

            for col in columns:
                _validate_identifier(col, "Column")

            column_sql = ", ".join(columns)

        elif isinstance(columns, str):
            if columns != "*":
                raise SQLBuilderError(
                    "Columns must be '*' or a list of column names"
                )
            column_sql = columns
        else:
            raise SQLBuilderError("Invalid columns parameter")

        # ---------- Build base query ----------
        query = f"SELECT {column_sql} FROM {table}"

        # ---------- WHERE clause ----------
        if where:
            if not isinstance(where, str):
                raise SQLBuilderError("WHERE clause must be a string")
            query += f" WHERE {where}"

        return query + ";"

    except Exception as exc:
        if isinstance(exc, SQLBuilderError):
            raise
        raise SQLBuilderError(f"SQL query build failed: {exc}") from exc
