from __future__ import annotations

from typing import Callable, Any, Optional
import time


class ETLError(Exception):
    """Raised when ETL pipeline execution fails."""


def run_etl(
    extract_fn: Callable[[], Any],
    transform_fn: Callable[[Any], Any],
    load_fn: Callable[[Any], None],
    *,
    strict: bool = True,
    measure_time: bool = False,
) -> bool:
    """
    Enterprise-grade ETL pipeline executor.

    Parameters
    ----------
    extract_fn : Callable
        Function that extracts raw data
    transform_fn : Callable
        Function that transforms extracted data
    load_fn : Callable
        Function that loads transformed data
    strict : bool, optional
        If True, fail-fast on any error (default True)
    measure_time : bool, optional
        If True, measures ETL execution time

    Returns
    -------
    bool
        True if ETL completed successfully

    Raises
    ------
    ETLError
        If any ETL stage fails (strict mode)
    """

    # ---------- Validation ----------
    if not callable(extract_fn):
        raise ETLError("extract_fn must be callable")

    if not callable(transform_fn):
        raise ETLError("transform_fn must be callable")

    if not callable(load_fn):
        raise ETLError("load_fn must be callable")

    start_time: Optional[float] = time.time() if measure_time else None

    try:
        # ---------- Extract ----------
        data = extract_fn()

        # ---------- Transform ----------
        data = transform_fn(data)

        # ---------- Load ----------
        load_fn(data)

        if measure_time and start_time is not None:
            elapsed = round(time.time() - start_time, 4)
            print(f"[datavitals] ETL completed in {elapsed}s")

        return True

    except Exception as exc:
        if strict:
            raise ETLError(f"ETL pipeline failed: {exc}") from exc

        # Non-strict mode → log & continue
        print(f"[datavitals][WARN] ETL error ignored: {exc}")
        return False
