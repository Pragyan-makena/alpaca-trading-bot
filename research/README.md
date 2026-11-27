# Offline historical market-data analysis

This folder is a separate, read-only research utility. It works with CSV files you already have on your computer. It does not connect to Alpaca, another broker, Discord, or any network service. It does not place orders, generate buy/sell signals, or recommend investments.

## Setup

From the repository root, install the existing project requirements:

    python -m pip install -r requirements.txt

The research tools only need pandas and matplotlib from that list.

## Input data

Put one CSV per symbol in research/data/input/, for example:

    research/data/input/SPY.csv
    research/data/input/QQQ.csv

Each CSV must contain a date column (Date, Datetime, or Timestamp) and a price column (Adj Close or Close). Adjusted close is preferred when supplied. A Volume column is optional.

The tool does not download data. Obtain files from a source whose terms permit your intended use. Keep raw data files out of Git unless you have checked redistribution rights.

## Generate a report

From the repository root:

    python -m research.run_report

Or specify folders:

    python -m research.run_report --input-dir path/to/csvs --output-dir path/to/report

The report folder contains:
- report.md — descriptive summary and embedded charts
- historical_summary.csv — one row of historical statistics per input file
- indexed_prices.png — price series rebased to 100 at each file's first observation
- historical_declines.png — historical peak-to-trough declines
- daily_change_correlation.png — daily price-change correlations when two or more files are supplied

## Data checks

The loader checks missing or invalid dates, missing or non-positive prices, duplicate dates, and unusually large daily moves. It reports large moves for human review instead of silently deleting them. It does not assume that every calendar day should have a market observation.

Run the tests:

    python -m unittest discover -s research/tests -v

## Scope

These outputs describe historical data. They are not forecasts, investment advice, trading signals, strategy comparisons, or evidence that a future outcome will resemble the past. The tool does not tune parameters or select a strategy.
