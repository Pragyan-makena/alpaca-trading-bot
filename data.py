from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed
from datetime import datetime, timedelta

from config import API_KEY, SECRET_KEY, SYMBOL


client = StockHistoricalDataClient(
    API_KEY,
    SECRET_KEY
)


def get_stock_data():

    end = datetime.now()

    start = end - timedelta(days=1500)


    request = StockBarsRequest(
        symbol_or_symbols=SYMBOL,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        feed=DataFeed.IEX
    )


    bars = client.get_stock_bars(
        request
    )


    data = bars.df


    if "symbol" in data.index.names:

        data = data.reset_index()


    data = data.sort_index()


    return data