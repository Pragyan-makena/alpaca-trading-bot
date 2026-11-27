from data import get_stock_data
from strategy import trend_signal
from trader import get_account, get_position, buy, sell, is_market_open, has_open_order
from risk_manager import calculate_position_size
from logger import log
from notifier import send_discord_message as notify  # swapped for the phone notifier later
from config import SYMBOLS


def process_symbol(symbol, equity):
    log(f"--- {symbol} ---")
    try:
        if has_open_order(symbol):
            log(f"{symbol}: open order pending, skipping")
            return

        data = get_stock_data(symbol)
        signal = trend_signal(data)
        price = float(data.iloc[-1]["close"])
        position = get_position(symbol)
        log(f"Signal: {signal} | Position: {position} | Last close: {price:.2f}")

        if signal == "BUY" and position == 0:
            shares = calculate_position_size(equity, price)
            if shares > 0:
                buy(symbol, shares)
                notify(f"🟢 BUY {symbol}: order for {shares} shares (last close ${price:.2f})")
        elif signal == "SELL" and position > 0:
            sell(symbol, position)
            notify(f"🔴 SELL {symbol}: order for {position:g} shares (last close ${price:.2f}), trend broke")
        else:
            log(f"{symbol}: no trade")
    except Exception as e:
        log(f"ERROR on {symbol}: {e}")
        notify(f"⚠️ Bot error on {symbol}: {e}")


def main():
    log("Starting Alpaca paper trend bot")
    try:
        if not is_market_open():
            log("Market closed, exiting")
            return
        equity = float(get_account().equity)
        for symbol in SYMBOLS:
            process_symbol(symbol, equity)
    except Exception as e:
        notify(f"⚠️ Bot crashed: {e}")
        raise


if __name__ == "__main__":
    main()
