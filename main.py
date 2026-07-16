from data import get_stock_data
from strategy import moving_average_strategy
from trader import (
    get_account,
    get_position,
    buy,
    sell
)
from risk_manager import (
    calculate_position_size,
    check_risk
)
from logger import log


def get_entry_price(position_obj):
    """Alpaca position object has avg_entry_price when a position is open."""
    try:
        return float(position_obj.avg_entry_price)
    except Exception:
        return None


def main():
    log("Starting Alpaca Paper Trading Bot")

    data = get_stock_data()
    signal = moving_average_strategy(data)

    account = get_account()
    balance = float(account.equity)
    price = data.iloc[-1]["close"]
    position = get_position()

    log(f"Signal: {signal}")
    log(f"Position: {position}")
    log(f"Current price: {price}")

    # --- Risk check first: if holding, see if stop-loss/take-profit triggers ---
    if position > 0:
        from trader import client
        from config import SYMBOL
        try:
            pos_obj = client.get_open_position(SYMBOL)
            entry_price = float(pos_obj.avg_entry_price)
            risk_result = check_risk(entry_price, price)
            log(f"Entry price: {entry_price} | Risk check: {risk_result}")

            if risk_result in ("STOP_LOSS", "TAKE_PROFIT"):
                sell(position)
                log(f"Exited position due to {risk_result}")
                return  # done for this run
        except Exception as e:
            log(f"Risk check skipped (no position data): {e}")

    # --- Strategy signal handling ---
    if signal == "BUY" and position == 0:
        shares = calculate_position_size(balance, price)
        if shares > 0:
            buy(shares)
        else:
            log("Position size calculated as 0, skipping buy")
    elif signal == "SELL" and position > 0:
        sell(position)
    else:
        log("No trade")


if __name__ == "__main__":
    main()