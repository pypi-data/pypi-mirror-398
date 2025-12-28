"""
datavitals

A reusable data engineering helper library that standardizes
data cleaning, ETL pipelines, and SQL query building.

Project Name : datavitals
Author       : Kamaleshkumar.K
Version      : 0.1.0
License      : MIT
"""

# -------------------------
# Library Metadata
# -------------------------
__project_name__: str = "datavitals"
__author__: str = "Kamaleshkumar.K"
__version__: str = "0.1.0"
__license__: str = "MIT"

# -------------------------
# Safe Public API Imports
# -------------------------
try:
    from .cleaning import clean_dataframe
    from .etl import run_etl
    from .sql_builder import select_query
except ImportError as exc:  # defensive guard
    raise ImportError(
        "datavitals package import failed. "
        "Ensure all internal modules are present and error-free."
    ) from exc

# -------------------------
# Explicit Public Interface
# -------------------------
__all__ = [
    "clean_dataframe",
    "run_etl",
    "select_query",
    "__project_name__",
    "__author__",
    "__version__",
    "__license__",
]