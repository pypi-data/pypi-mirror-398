"""
datavitals

A reusable data engineering helper library that standardizes
data cleaning, ETL pipelines, and SQL query building.

Project Name : datavitals
Author       : Kamaleshkumar.K
GitHub       : https://github.com/kamaleshkumaroffi/datavitals
LinkedIn     : https://www.linkedin.com/in/kamaleshkumaroffi
Version      : 0.1.0
License      : MIT
"""

# -------------------------
# Library Metadata
# -------------------------
__project_name__: str = "datavitals"
__author__: str = "Kamaleshkumar.K"
__github__: str = "https://github.com/kamaleshkumaroffi/datavitals"
__linkedin__: str = "https://www.linkedin.com/in/kamaleshkumaroffi"
__version__: str = "0.1.0"
__license__: str = "MIT"

# -------------------------
# Safe Public API Imports
# -------------------------
try:
    from .cleaning import clean_dataframe
    from .etl import run_etl
    from .sql_builder import select_query
except Exception as exc:
    raise ImportError(
        "datavitals failed to initialize. "
        "Check internal modules: cleaning, etl, sql_builder."
    ) from exc

# -------------------------
# Explicit Public Interface
# -------------------------
__all__ = [
    # Public APIs
    "clean_dataframe",
    "run_etl",
    "select_query",

    # Metadata
    "__project_name__",
    "__author__",
    "__github__",
    "__linkedin__",
    "__version__",
    "__license__",
]
