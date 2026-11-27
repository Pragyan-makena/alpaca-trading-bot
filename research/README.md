# Historical research data

This folder contains a read-only historical market-data downloader for SPY, QQQ, DIA, and IWM.

## Run locally

Install the dependencies:

```bash
python -m pip install alpaca-py pandas pandas-market-calendars python-dotenv
```

Set `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` in the repository-root `.env` file, then run:

```bash
python research/fetch_data.py
```

The script writes CSVs and `manifest.json` under `research/data/`. That directory is git-ignored.

## Run through GitHub Actions

After the workflow is merged into the default branch, open **Actions → Download Historical Research Data → Run workflow**. It uses the existing `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` repository Actions secrets and uploads the files as a 14-day artifact.

The workflow only calls Alpaca's historical stock-bars data endpoint. It does not import the trading client or submit orders.

## Output conventions

For each ticker, two files are produced:

- `*_split_adjusted.csv`: split-adjusted daily OHLCV.
- `*_total_return_adjusted.csv`: split- and dividend-adjusted daily OHLCV.

The total-return-adjusted series is useful for total-return research, but its adjusted OHLC values should not be treated as literal executable fill prices. The manifest records the feed, date range, row counts, and any missing NYSE sessions.

The selected IEX feed represents a single exchange rather than consolidated US-market volume. Keep that limitation in mind when interpreting results.
