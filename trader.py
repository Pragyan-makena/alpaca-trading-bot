from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from config import API_KEY, SECRET_KEY, PAPER_TRADING
from logger import log

client = TradingClient(API_KEY, SECRET_KEY, paper=PAPER_TRADING)


def get_account():
    return client.get_account()


def is_market_open():
    return client.get_clock().is_open


def has_open_order(symbol):
    req = GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[symbol])
    return len(client.get_orders(req)) > 0


def get_position(symbol):
    try:
        return float(client.get_open_position(symbol).qty)
    except Exception:
        return 0


def _submit(symbol, quantity, side):
    if quantity <= 0:
        return None
    order = client.submit_order(MarketOrderRequest(
        symbol=symbol, qty=quantity, side=side, time_in_force=TimeInForce.DAY
    ))
    log(f"{side.value.upper()} {quantity} {symbol} (order {order.id})")
    return order


def buy(symbol, quantity):
    return _submit(symbol, quantity, OrderSide.BUY)


def sell(symbol, quantity):
    return _submit(symbol, quantity, OrderSide.SELL)
