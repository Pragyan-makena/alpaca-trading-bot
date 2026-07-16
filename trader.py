from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from config import (
    API_KEY,
    SECRET_KEY,
    PAPER_TRADING
)
from logger import log

client = TradingClient(
    API_KEY,
    SECRET_KEY,
    paper=PAPER_TRADING
)


def get_account():
    return client.get_account()


def get_position(symbol):
    try:
        position = client.get_open_position(symbol)
        return float(position.qty)
    except Exception:
        return 0


def get_entry_price(symbol):
    try:
        position = client.get_open_position(symbol)
        return float(position.avg_entry_price)
    except Exception:
        return None


def buy(symbol, quantity):
    if quantity <= 0:
        return
    order = MarketOrderRequest(
        symbol=symbol,
        qty=quantity,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
    client.submit_order(order)
    log(f"BUY {quantity} shares of {symbol}")


def sell(symbol, quantity):
    if quantity <= 0:
        return
    order = MarketOrderRequest(
        symbol=symbol,
        qty=quantity,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY
    )
    client.submit_order(order)
    log(f"SELL {quantity} shares of {symbol}")