"""Download completed daily ETF bars for offline research only.

This module uses Alpaca's historical market-data endpoint. It does not import
TradingClient and contains no order-submission code.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pandas_market_calendars as mcal
from dotenv import load_dotenv

from alpaca.common.enums import PaginationType
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path(os.getenv("RESEARCH_DATA_DIR", ROOT / "research" / "data"))
SYMBOLS = ("SPY", "QQQ", "DIA", "IWM")
START_DATE = "2016-01-01"
NEW_YORK = "America/New_York"
CLOSE_BUFFER_MINUTES = 30
ADJUSTMENTS = {
    "split_adjusted": Adjustment.SPLIT,
    "total_return_adjusted": Adjustment.ALL,
}


def build_client() -> StockHistoricalDataClient:
    """Build a read-only historical market-data client from environment keys."""
    load_dotenv(ROOT / ".env")
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_SECRET_KEY")
    if not key or not secret:
        raise RuntimeError(
            "Missing ALPACA_API_KEY or ALPACA_SECRET_KEY. "
            "Set them in your local .env or the GitHub Actions secrets."
        )
    return StockHistoricalDataClient(api_key=key, secret_key=secret)


def last_completed_session() -> tuple[datetime, datetime.date, list[datetime.date]]:
    """Return the most recent NYSE close at least 30 minutes in the past."""
    now_utc = pd.Timestamp.now(tz="UTC")
    cutoff = now_utc - pd.Timedelta(minutes=CLOSE_BUFFER_MINUTES)
    today_ny = now_utc.tz_convert(NEW_YORK).date()

    calendar = mcal.get_calendar("NYSE")
    schedule = calendar.schedule(
        start_date=START_DATE,
        end_date=today_ny.isoformat(),
    )
    completed = schedule.loc[schedule["market_close"] <= cutoff]
    if completed.empty:
        raise RuntimeError("No completed NYSE session is available yet.")

    last_close = completed["market_close"].iloc[-1].to_pydatetime()
    last_date = completed.index[-1].date()
    expected_dates = [stamp.date() for stamp in completed.index]
    return last_close, last_date, expected_dates


def normalize_bars(bars, symbol: str) -> pd.DataFrame:
    frame = bars.df.reset_index()
    if "timestamp" not in frame.columns:
        raise ValueError(f"{symbol}: Alpaca response has no timestamp column.")

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"], utc=True, errors="raise"
    )
    frame["session_date"] = (
        frame["timestamp"].dt.tz_convert(NEW_YORK).dt.date
    )

    numeric = ["open", "high", "low", "close", "volume"]
    missing_columns = set(numeric) - set(frame.columns)
    if missing_columns:
        raise ValueError(
            f"{symbol}: response is missing columns {sorted(missing_columns)}"
        )

    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if frame[numeric].isna().any().any():
        raise ValueError(f"{symbol}: OHLCV contains missing/non-numeric values.")
    if (frame[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError(f"{symbol}: non-positive price found.")
    if (frame["volume"] < 0).any():
        raise ValueError(f"{symbol}: negative volume found.")
    if (frame["high"] < frame[["open", "close", "low"]].max(axis=1)).any():
        raise ValueError(f"{symbol}: inconsistent high price found.")
    if (frame["low"] > frame[["open", "close", "high"]].min(axis=1)).any():
        raise ValueError(f"{symbol}: inconsistent low price found.")
    if frame["session_date"].duplicated().any():
        raise ValueError(f"{symbol}: duplicate daily session found.")

    frame["symbol"] = symbol
    keep = [
        "symbol", "timestamp", "session_date",
        "open", "high", "low", "close", "volume",
    ]
    for optional in ("trade_count", "vwap"):
        if optional in frame.columns:
            keep.append(optional)

    return frame[keep].sort_values("timestamp").reset_index(drop=True)


def download_one(
    client: StockHistoricalDataClient,
    symbol: str,
    adjustment_name: str,
    adjustment: Adjustment,
    last_close: datetime,
    last_date,
    expected_dates: list[datetime.date],
) -> dict:
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=datetime(2016, 1, 1, tzinfo=timezone.utc),
        end=last_close + timedelta(seconds=1),
        limit=10_000,
        adjustment=adjustment,
        feed=DataFeed.IEX,
    )

    # FULL follows every next_page_token; 10,000 is the API page-size limit.
    bars = client.get_stock_bars(
        request,
        handle_pagination=PaginationType.FULL,
    )
    frame = normalize_bars(bars, symbol)

    if frame.empty:
        raise RuntimeError(f"{symbol}: Alpaca returned no daily bars.")

    actual_dates = set(frame["session_date"])
    missing_dates = [
        day.isoformat() for day in expected_dates if day not in actual_dates
    ]
    latest_date = max(actual_dates)

    if latest_date != last_date:
        raise RuntimeError(
            f"{symbol}: latest returned session is {latest_date}, "
            f"but the latest completed NYSE session is {last_date}. "
            "No file was accepted; check feed access and retry."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{symbol}_{adjustment_name}.csv"
    path = OUTPUT_DIR / filename
    frame.to_csv(path, index=False)

    print(
        f"{symbol} ({adjustment_name}): {len(frame)} rows; "
        f"{frame['session_date'].min()} to {latest_date}; "
        f"{len(missing_dates)} missing exchange sessions."
    )

    return {
        "symbol": symbol,
        "adjustment": adjustment_name,
        "rows": int(len(frame)),
        "first_session": frame["session_date"].min().isoformat(),
        "last_session": latest_date.isoformat(),
        "missing_session_count": len(missing_dates),
        "missing_sessions_sample": missing_dates[:20],
        "file": filename,
    }


def main() -> None:
    print("Historical data download: read-only; no orders are submitted.")
    client = build_client()
    last_close, last_date, expected_dates = last_completed_session()

    print(f"Feed: IEX | latest completed NYSE session: {last_date}")
    results = []
    for symbol in SYMBOLS:
        for adjustment_name, adjustment in ADJUSTMENTS.items():
            results.append(
                download_one(
                    client,
                    symbol,
                    adjustment_name,
                    adjustment,
                    last_close,
                    last_date,
                    expected_dates,
                )
            )

    manifest = {
        "source": "Alpaca historical stock bars",
        "feed": "IEX",
        "timeframe": "1Day",
        "start_date": START_DATE,
        "latest_completed_nyse_session": last_date.isoformat(),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "adjustments": {
            "split_adjusted": "Splits adjusted; dividends not reinvested.",
            "total_return_adjusted": (
                "Splits and dividends adjusted. Use for total-return "
                "analysis, not as literal executable fill prices."
            ),
        },
        "results": results,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Download complete. Files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
