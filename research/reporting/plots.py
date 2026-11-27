"""Static charts for descriptive, historical price analysis."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def write_charts(
    series: Mapping[str, pd.DataFrame],
    output_dir: str | Path,
) -> list[str]:
    """Write indexed-price, historical-decline, and optional correlation plots."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    normalized = pd.DataFrame({
        symbol: frame["price"] / frame["price"].iloc[0] * 100.0
        for symbol, frame in series.items()
    })
    fig, ax = plt.subplots(figsize=(10, 5))
    normalized.plot(ax=ax)
    ax.set_title("Historical price change (each series starts at 100)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Indexed price")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = destination / "indexed_prices.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    written.append(path.name)

    fig, ax = plt.subplots(figsize=(10, 5))
    for symbol, frame in series.items():
        drawdown = frame["price"] / frame["price"].cummax() - 1.0
        ax.plot(drawdown.index, drawdown * 100.0, label=symbol)
    ax.set_title("Historical peak-to-trough declines")
    ax.set_xlabel("Date")
    ax.set_ylabel("Decline from prior peak (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = destination / "historical_declines.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    written.append(path.name)

    if len(series) >= 2:
        returns = pd.DataFrame({
            symbol: frame["price"].pct_change()
            for symbol, frame in series.items()
        })
        correlation = returns.corr()
        fig, ax = plt.subplots(figsize=(7, 6))
        image = ax.imshow(correlation, vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(len(correlation.columns)), labels=correlation.columns, rotation=45, ha="right")
        ax.set_yticks(range(len(correlation.index)), labels=correlation.index)
        ax.set_title("Correlation of daily historical price changes")
        fig.colorbar(image, ax=ax, label="Correlation")
        fig.tight_layout()
        path = destination / "daily_change_correlation.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        written.append(path.name)

    return written
