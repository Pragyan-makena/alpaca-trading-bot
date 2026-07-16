from data import get_stock_data
from strategy import moving_average_strategy
from trader import (
    get_account,
    get_position,
    get_entry_price,
    buy,
    sell
)
from risk_manager import (
    calculate_position_size,
    check_risk
)
from logger import log
from notifier import send_discord_message
from config import SYMBOLS


def process_symbol(symbol, balance):
    log(f"--- {symbol} ---")

    try:
        data = get_stock_data(symbol)
        signal = moving_average_strategy(data)
        price = data.iloc[-1]["close"]
        position = get_position(symbol)

        log(f"Signal: {signal}")
        log(f"Position: {position}")
        log(f"Current price: {price}")

        if position > 0:
            entry_price = get_entry_price(symbol)
            if entry_price is not None:
                risk_result = check_risk(entry_price, price)
                log(f"Entry price: {entry_price} | Risk check: {risk_result}")

                if risk_result in ("STOP_LOSS", "TAKE_PROFIT"):
                    sell(symbol, position)
                    log(f"{symbol}: exited due to {risk_result}")
                    send_discord_message(
                        f"🔴 **{risk_result}** on {symbol}\n"
                        f"Sold {position} shares at ${price:.2f}\n"
                        f"Entry was ${entry_price:.2f}"
                    )
                    return

        if signal == "BUY" and position == 0:
            shares = calculate_position_size(balance, price)
            if shares > 0:
                buy(symbol, shares)
                send_discord_message(
                    f"🟢 **BUY** on {symbol}\n"
                    f"Bought {shares} shares at ${price:.2f}"
                )
            else:
                log(f"{symbol}: position size 0, skipping buy")
        elif signal == "SELL" and position > 0:
            sell(symbol, position)
            send_discord_message(
                f"🔵 **SELL** on {symbol} (MA crossover)\n"
                f"Sold {position} shares at ${price:.2f}"
            )
        else:
            log(f"{symbol}: no trade")

    except Exception as e:
        log(f"ERROR on {symbol}: {e}")
        send_discord_message(f"⚠️ **Bot error** on {symbol}: {e}")


def main():
    log("Starting Alpaca Paper Trading Bot")

    account = get_account()
    balance = float(account.equity)

    for symbol in SYMBOLS:
        process_symbol(symbol, balance)


if __name__ == "__main__":
    main()