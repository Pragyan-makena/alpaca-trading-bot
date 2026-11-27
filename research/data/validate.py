"""Normalize and validate local historical price CSV files.

This module is deliberately offline: it reads files supplied by the user and
never connects to a data provider or brokerage.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


DATE_NAMES = ("date", "datetime", "timestamp")
ADJUSTED_PRICE_NAMES = ("adj_close", "adjusted_close", "adjclose", "adjustedclose")
CLOSE_NAMES = ("close", "closing_price")
VOLUME_NAMES = ("volume",)


def _normalized_name(value: object) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def _find_column(columns: Iterable[object], names: Iterable[str]) -> object | None:
    lookup = {_normalized_name(column): column for column in columns}
    for name in names:
        if name in lookup:
            return lookup[name]
    return None


def normalize_price_frame(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str], str]:
    """Return a clean frame indexed by date, warnings, and selected price column.

    Adjusted close is preferred when available. Invalid dates/prices are
    excluded; duplicate dates keep the final row after stable date sorting.
    Large one-day moves are reported for review, not silently removed.
    """
    if raw.empty:
        raise ValueError("The CSV contains no data rows.")

    date_col = _find_column(raw.columns, DATE_NAMES)
    adjusted_col = _find_column(raw.columns, ADJUSTED_PRICE_NAMES)
    close_col = _find_column(raw.columns, CLOSE_NAMES)
    volume_col = _find_column(raw.columns, VOLUME_NAMES)
    price_col = adjusted_col if adjusted_col is not None else close_col

    if date_col is None:
        raise ValueError("A Date, Datetime, or Timestamp column is required.")
    if price_col is None:
        raise ValueError("A Close or Adj Close column is required.")

    warnings: list[str] = []
    dates = pd.to_datetime(raw[date_col], errors="coerce", utc=True).dt.tz_convert(None)
    prices = pd.to_numeric(raw[price_col], errors="coerce")

    clean = pd.DataFrame({"date": dates, "price": prices})
    if volume_col is not None:
        clean["volume"] = pd.to_numeric(raw[volume_col], errors="coerce")

    bad_dates = int(clean["date"].isna().sum())
    bad_prices = int((clean["price"].isna() | (clean["price"] <= 0)).sum())
    if bad_dates:
        warnings.append(f"Excluded {bad_dates} row(s) with invalid dates.")
    if bad_prices:
        warnings.append(f"Excluded {bad_prices} row(s) with missing or non-positive prices.")

    clean = clean.dropna(subset=["date", "price"])
    clean = clean.loc[clean["price"] > 0].sort_values("date", kind="stable")

    duplicate_count = int(clean["date"].duplicated(keep="last").sum())
    if duplicate_count:
        warnings.append(f"Found {duplicate_count} duplicate date row(s); kept the last row per date.")
        clean = clean.drop_duplicates(subset=["date"], keep="last")

    clean = clean.set_index("date").sort_index()
    if clean.empty:
        raise ValueError("No valid dated, positive prices remain after validation.")

    daily_moves = clean["price"].pct_change().dropna()
    large_moves = int((daily_moves.abs() > 0.20).sum())
    if large_moves:
        warnings.append(
            f"Found {large_moves} daily price move(s) above 20%; review the source data "
            "and corporate-action adjustments."
        )

    return clean, warnings, str(price_col)


def read_price_csv(path: str | Path) -> tuple[pd.DataFrame, list[str], str]:
    """Read and normalize one local CSV file."""
    source = Path(path)
    raw = pd.read_csv(source)
    return normalize_price_frame(raw)
