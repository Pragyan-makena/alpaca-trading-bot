import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed
from datetime import datetime, timedelta
from config import API_KEY, SECRET_KEY

client = StockHistoricalDataClient(API_KEY, SECRET_KEY)


def drop_incomplete_bar(df):
    """Remove today's still-forming daily bar so signals use completed closes only."""
    today = pd.Timestamp.now(tz="America/New_York").normalize().tz_localize(None)
    idx = df.index.tz_convert("America/New_York").tz_localize(None).normalize()
    return df[idx < today]


def get_stock_data(symbol):
    end = datetime.now()
    start = end - timedelta(days=700)  # ~480 trading days, plenty for a 200-day SMA
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        feed=DataFeed.IEX,
    )
    df = client.get_stock_bars(request).df
    if isinstance(df.index, pd.MultiIndex):
        df = df.xs(symbol, level="symbol")
    return drop_incomplete_bar(df.sort_index())
