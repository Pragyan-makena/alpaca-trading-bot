"""
backtest_final.py - the final strategy (200-day SMA + 1% band) vs buy-and-hold,
on real Alpaca daily data. Signal at close t -> position held on t+1 (no lookahead).
Run: python backtest_final.py
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed
from config import API_KEY, SECRET_KEY, SYMBOLS, SMA_WINDOW, BAND

COST = 0.0005  # 5 bps per switch (slippage buffer; Alpaca is commission-free)


def load(symbol, years=8):
    end = datetime.now()
    req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day,
                           start=end - timedelta(days=365 * years), end=end, feed=DataFeed.IEX)
    df = StockHistoricalDataClient(API_KEY, SECRET_KEY).get_stock_bars(req).df
    if isinstance(df.index, pd.MultiIndex):
        df = df.xs(symbol, level="symbol")
    return df["close"].sort_index()


def strategy_returns(close, window=SMA_WINDOW, band=BAND, cost=COST):
    sma = close.rolling(window).mean()
    state, states = 0, []
    for c, s in zip(close, sma):
        if not np.isnan(s):
            if c > s * (1 + band):
                state = 1
            elif c < s * (1 - band):
                state = 0
        states.append(state)
    pos = pd.Series(states, index=close.index).shift(1).fillna(0)
    ret = close.pct_change().fillna(0) * pos - pos.diff().abs().fillna(0) * cost
    return ret[sma.notna()], close.pct_change().fillna(0)[sma.notna()], int(pos.diff().abs().sum())


def stats(r):
    eq = (1 + r).cumprod()
    yrs = len(r) / 252
    return {"CAGR": eq.iloc[-1] ** (1 / yrs) - 1,
            "MaxDD": (eq / eq.cummax() - 1).min(),
            "Sharpe": r.mean() / r.std() * np.sqrt(252) if r.std() else 0}


def show(name, s, b, switches=None):
    extra = f" | switches {switches}" if switches is not None else ""
    print(f"{name:<10} strat CAGR {s['CAGR']:6.1%} DD {s['MaxDD']:6.1%} Sharpe {s['Sharpe']:4.2f}"
          f"  ||  buy&hold CAGR {b['CAGR']:6.1%} DD {b['MaxDD']:6.1%} Sharpe {b['Sharpe']:4.2f}{extra}")


def main():
    strat, bh = {}, {}
    for sym in SYMBOLS:
        s, b, sw = strategy_returns(load(sym))
        strat[sym], bh[sym] = s, b
        show(sym, stats(s), stats(b), sw)
    ps = pd.DataFrame(strat).dropna().mean(axis=1)
    pb = pd.DataFrame(bh).dropna().mean(axis=1)
    print()
    show("PORTFOLIO", stats(ps), stats(pb))
    print("\nSensitivity (SPY): window x band")
    spy = load("SPY")
    for w in (150, 200, 250):
        for bnd in (0.0, 0.01, 0.02):
            s, _, _ = strategy_returns(spy, w, bnd)
            st = stats(s)
            print(f"SMA{w} band {bnd:.0%}: CAGR {st['CAGR']:6.1%} DD {st['MaxDD']:6.1%} Sharpe {st['Sharpe']:4.2f}")


if __name__ == "__main__":
    main()
