from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from config import (
    API_KEY,
    SECRET_KEY,
    PAPER_TRADING,
    SYMBOL
)

from logger import log



client = TradingClient(
    API_KEY,
    SECRET_KEY,
    paper=PAPER_TRADING
)



def get_account():

    return client.get_account()



def get_position():

    try:

        position = client.get_open_position(
            SYMBOL
        )

        return float(
            position.qty
        )

    except:

        return 0



def buy(quantity):

    if quantity <= 0:

        return


    order = MarketOrderRequest(
        symbol=SYMBOL,
        qty=quantity,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )


    client.submit_order(order)


    log(
        f"BUY {quantity} shares"
    )



def sell(quantity):

    if quantity <= 0:

        return


    order = MarketOrderRequest(
        symbol=SYMBOL,
        qty=quantity,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY
    )


    client.submit_order(order)


    log(
        f"SELL {quantity} shares"
    )