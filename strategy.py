import pandas as pd
from config import SMA_WINDOW, BAND


def add_indicators(data):
    data = data.copy()
    data["SMA"] = data["close"].rolling(SMA_WINDOW).mean()
    return data


def trend_signal(data):
    """BUY = clearly above the 200-day SMA, SELL = clearly below, HOLD = inside the band
    (or not enough history). main.py only buys when flat and only sells when holding."""
    data = add_indicators(data)
    if len(data) < SMA_WINDOW + 1:
        return "HOLD"
    last = data.iloc[-1]
    if pd.isna(last["SMA"]):
        return "HOLD"
    if last["close"] > last["SMA"] * (1 + BAND):
        return "BUY"
    if last["close"] < last["SMA"] * (1 - BAND):
        return "SELL"
    return "HOLD"
