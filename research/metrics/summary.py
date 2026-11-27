"""Descriptive statistics for one historical price series."""
from __future__ import annotations

import math

import pandas as pd


def summarize_prices(frame: pd.DataFrame) -> dict[str, float | int | str]:
    """Summarize historical price movements; does not evaluate a strategy."""
    if frame.empty or "price" not in frame:
        raise ValueError("Expected a non-empty frame with a 'price' column.")

    prices = pd.to_numeric(frame["price"], errors="coerce").dropna()
    prices = prices.loc[prices > 0].sort_index()
    if len(prices) < 2:
        raise ValueError("At least two valid price observations are required.")

    changes = prices.pct_change().dropna()
    drawdowns = prices.div(prices.cummax()).sub(1.0)
    volatility = float(changes.std(ddof=1) * math.sqrt(252)) if len(changes) > 1 else float("nan")

    result: dict[str, float | int | str] = {
        "start_date": prices.index[0].date().isoformat(),
        "end_date": prices.index[-1].date().isoformat(),
        "observations": int(len(prices)),
        "first_price": float(prices.iloc[0]),
        "last_price": float(prices.iloc[-1]),
        "price_change_pct": float((prices.iloc[-1] / prices.iloc[0] - 1.0) * 100.0),
        "annualized_daily_volatility_pct": volatility * 100.0,
        "maximum_peak_to_trough_decline_pct": float(drawdowns.min() * 100.0),
        "best_daily_change_pct": float(changes.max() * 100.0),
        "worst_daily_change_pct": float(changes.min() * 100.0),
        "average_daily_change_pct": float(changes.mean() * 100.0),
    }

    if "volume" in frame:
        volume = pd.to_numeric(frame["volume"], errors="coerce").dropna()
        result["average_reported_volume"] = float(volume.mean()) if not volume.empty else float("nan")

    return result
