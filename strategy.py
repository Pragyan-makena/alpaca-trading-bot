import pandas as pd
from config import SHORT_WINDOW, LONG_WINDOW


def add_indicators(data):
    data["MA20"] = data["close"].rolling(SHORT_WINDOW).mean()
    data["MA50"] = data["close"].rolling(LONG_WINDOW).mean()
    return data


def moving_average_strategy(data):
    data = add_indicators(data)

    if len(data) < LONG_WINDOW + 1:
        return "HOLD"

    yesterday = data.iloc[-2]
    today = data.iloc[-1]

    if yesterday.MA20 < yesterday.MA50 and today.MA20 > today.MA50:
        return "BUY"
    if yesterday.MA20 > yesterday.MA50 and today.MA20 < today.MA50:
        return "SELL"
    return "HOLD"