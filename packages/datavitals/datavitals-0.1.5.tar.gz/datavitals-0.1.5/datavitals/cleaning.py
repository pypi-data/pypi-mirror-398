from __future__ import annotations

import pandas as pd
from pandas.api.types import is_numeric_dtype
from typing import Final

# Optional: internal constant (future extension ready)
_EMPTY_ROW_POLICY: Final[str] = "drop"


class DataCleaningError(Exception):
    """Raised when DataFrame cleaning fails."""


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enterprise-grade DataFrame cleaning utility.

    Operations performed:
    - Validate input type
    - Deep copy original DataFrame (immutability)
    - Remove duplicate rows
    - Safely convert numeric-like columns
    - Drop rows where all values are NaN

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame to clean

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame

    Raises
    ------
    DataCleaningError
        If cleaning fails due to unexpected reasons
    """

    # ---------- Validation ----------
    if not isinstance(df, pd.DataFrame):
        raise DataCleaningError(
            f"clean_dataframe expects pandas DataFrame, got {type(df).__name__}"
        )

    try:
        # ---------- Defensive Copy ----------
        cleaned_df = df.copy(deep=True)

        # ---------- Remove Duplicates ----------
        cleaned_df.drop_duplicates(inplace=True)

        # ---------- Safe Numeric Conversion ----------
        for col in cleaned_df.columns:
            if not is_numeric_dtype(cleaned_df[col]):
                try:
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col])
                except (ValueError, TypeError):
                    # Non-numeric columns intentionally ignored
                    continue

        # ---------- Handle Empty Rows ----------
        if _EMPTY_ROW_POLICY == "drop":
            cleaned_df.dropna(how="all", inplace=True)

        return cleaned_df

    except Exception as exc:
        raise DataCleaningError(
            f"Data cleaning failed due to unexpected error: {exc}"
        ) from exc
