from data import get_stock_data
from strategy import moving_average_strategy
from trader import (
    get_account,
    get_position,
    buy,
    sell
)
from risk_manager import (
    calculate_position_size
)
from logger import log


def main():
    log("Starting Alpaca Paper Trading Bot")

    data = get_stock_data()
    signal = moving_average_strategy(data)

    account = get_account()
    balance = float(account.equity)
    price = data.iloc[-1]["close"]
    position = get_position()
    shares = calculate_position_size(balance, price)

    log(f"Signal: {signal}")
    log(f"Position: {position}")

    if signal == "BUY" and position == 0:
        buy(shares)
    elif signal == "SELL" and position > 0:
        sell(position)
    else:
        log("No trade")


if __name__ == "__main__":
    main()