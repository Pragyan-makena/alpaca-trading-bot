"""
backtest.py - Multi-symbol walk-forward validation with robustness scoring
Paper/backtest only. No live trading. Alpaca IEX feed only.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")

SYMBOLS = ["SPY", "QQQ", "DIA"]
YEARS_HISTORY = 8
START_DATE = datetime.now() - timedelta(days=365 * YEARS_HISTORY)
END_DATE = datetime.now()
STARTING_CASH = 10000
N_FOLDS = 6          # data split into 6 segments -> folds 1..5 used as out-of-sample tests
MIN_TOTAL_TRADES = 15  # ignore any combo without enough trades to trust stats

client = StockHistoricalDataClient(API_KEY, API_SECRET)


def get_data(symbol, start=START_DATE, end=END_DATE):
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        feed=DataFeed.IEX,
    )
    bars = client.get_stock_bars(request)
    df = bars.df
    if isinstance(df.index, pd.MultiIndex):
        df = df.xs(symbol, level=0)
    df = df[['close']].copy()
    df.index = pd.to_datetime(df.index)
    return df


def signals_from_df(df, fast, slow):
    df = df.copy()
    df['ma_fast'] = df['close'].rolling(fast).mean()
    df['ma_slow'] = df['close'].rolling(slow).mean()
    df['signal'] = 0
    df.loc[df['ma_fast'] > df['ma_slow'], 'signal'] = 1
    df['position'] = df['signal'].shift(1).fillna(0)
    df = df.dropna(subset=['ma_slow']).copy()
    return df


def simulate(df, stop_loss_pct=None, take_profit_pct=None, starting_cash=STARTING_CASH):
    """df must already have 'close' and 'position' columns, no NaNs."""
    if len(df) < 2:
        return None, None

    cash = starting_cash
    shares = 0
    entry_price = None
    equity_curve = []
    trades = []

    for i in range(len(df)):
        price = df['close'].iloc[i]
        pos = df['position'].iloc[i]
        date = df.index[i]
        exited_this_bar = False

        if shares > 0 and entry_price is not None:
            change_pct = (price - entry_price) / entry_price
            if stop_loss_pct is not None and change_pct <= -stop_loss_pct:
                cash += shares * price
                trades.append({'exit_price': price, 'entry_price': entry_price, 'reason': 'stop_loss'})
                shares = 0
                entry_price = None
                exited_this_bar = True
            elif take_profit_pct is not None and change_pct >= take_profit_pct:
                cash += shares * price
                trades.append({'exit_price': price, 'entry_price': entry_price, 'reason': 'take_profit'})
                shares = 0
                entry_price = None
                exited_this_bar = True

        if exited_this_bar:
            equity_curve.append({'date': date, 'equity': cash + shares * price})
            continue

        if pos == 1 and shares == 0:
            shares = cash // price
            if shares > 0:
                cash -= shares * price
                entry_price = price
        elif pos == 0 and shares > 0:
            cash += shares * price
            trades.append({'exit_price': price, 'entry_price': entry_price, 'reason': 'signal'})
            shares = 0
            entry_price = None

        equity_curve.append({'date': date, 'equity': cash + shares * price})

    if shares > 0:
        final_price = df['close'].iloc[-1]
        cash += shares * final_price
        trades.append({'exit_price': final_price, 'entry_price': entry_price, 'reason': 'end_of_fold'})

    equity_df = pd.DataFrame(equity_curve).set_index('date')
    return equity_df, trades


def fold_metrics(equity_df, trades, starting_cash):
    if equity_df is None or len(equity_df) < 2:
        return None

    ending_equity = equity_df['equity'].iloc[-1]
    total_return = (ending_equity - starting_cash) / starting_cash

    days = (equity_df.index[-1] - equity_df.index[0]).days
    years = days / 365.25 if days > 0 else (1 / 365.25)
    cagr = (ending_equity / starting_cash) ** (1 / years) - 1 if years > 0 and ending_equity > 0 else -1

    daily_returns = equity_df['equity'].pct_change().dropna()
    sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() not in (0, None) and len(daily_returns) > 1 else 0

    running_max = equity_df['equity'].cummax()
    drawdown = (equity_df['equity'] - running_max) / running_max
    max_drawdown = drawdown.min()

    trade_returns = [(t['exit_price'] - t['entry_price']) / t['entry_price'] for t in trades if t['entry_price'] is not None]
    num_trades = len(trade_returns)
    wins = sum(1 for r in trade_returns if r > 0)

    return {
        'return_pct': total_return * 100,
        'cagr_pct': cagr * 100,
        'sharpe': sharpe,
        'max_dd_pct': max_drawdown * 100,
        'num_trades': num_trades,
        'wins': wins,
    }


def run_walk_forward(symbol_data, fast, slow, stop_loss_pct=None, take_profit_pct=None):
    """symbol_data: dict of symbol -> raw price df. Returns list of fold metrics dicts."""
    all_fold_metrics = []

    for symbol, df in symbol_data.items():
        L = len(df)
        if L < 300:
            continue
        boundaries = [int(L * i / N_FOLDS) for i in range(N_FOLDS + 1)]

        for k in range(1, N_FOLDS):  # skip fold 0 (used only as lookback warmup)
            test_start_idx = boundaries[k]
            test_end_idx = boundaries[k + 1]
            test_start_date = df.index[test_start_idx]

            window_df = df.iloc[:test_end_idx]  # includes full lookback from start
            sig_df = signals_from_df(window_df, fast, slow)
            test_slice = sig_df[sig_df.index >= test_start_date]

            if len(test_slice) < 15:
                continue

            equity_df, trades = simulate(test_slice, stop_loss_pct, take_profit_pct, STARTING_CASH)
            m = fold_metrics(equity_df, trades, STARTING_CASH)
            if m is not None:
                m['symbol'] = symbol
                m['fold'] = k
                all_fold_metrics.append(m)

    return all_fold_metrics


def aggregate(fold_metrics_list, label):
    if not fold_metrics_list:
        return None

    total_trades = sum(m['num_trades'] for m in fold_metrics_list)
    total_wins = sum(m['wins'] for m in fold_metrics_list)
    avg_sharpe = np.mean([m['sharpe'] for m in fold_metrics_list])
    avg_return = np.mean([m['return_pct'] for m in fold_metrics_list])
    avg_dd = np.mean([m['max_dd_pct'] for m in fold_metrics_list])
    positive_folds = sum(1 for m in fold_metrics_list if m['return_pct'] > 0)
    consistency_pct = (positive_folds / len(fold_metrics_list)) * 100
    pooled_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0

    return {
        'label': label,
        'total_trades': total_trades,
        'avg_sharpe': round(avg_sharpe, 2),
        'avg_return_pct': round(avg_return, 2),
        'avg_max_dd_pct': round(avg_dd, 2),
        'consistency_pct': round(consistency_pct, 1),
        'pooled_win_rate_pct': round(pooled_win_rate, 1),
        'num_fold_tests': len(fold_metrics_list),
    }


def print_leaderboard(title, agg_results):
    print(f"\n=== {title} ===")
    print(f"{'Strategy':<26}{'Trades':>8}{'Sharpe':>9}{'Return%':>10}{'MaxDD%':>9}{'Consist%':>10}{'Win%':>8}{'Folds':>7}")
    for r in agg_results:
        print(f"{r['label']:<26}{r['total_trades']:>8}{r['avg_sharpe']:>9}{r['avg_return_pct']:>10}"
              f"{r['avg_max_dd_pct']:>9}{r['consistency_pct']:>10}{r['pooled_win_rate_pct']:>8}{r['num_fold_tests']:>7}")


FAST_OPTIONS = [5, 10, 15, 20, 25]
SLOW_OPTIONS = [30, 50, 100, 200]


def main():
    print(f"Fetching {YEARS_HISTORY} years of data for {SYMBOLS}...")
    symbol_data = {}
    for sym in SYMBOLS:
        df = get_data(sym)
        symbol_data[sym] = df
        print(f"{sym}: {len(df)} bars, {df.index[0].date()} to {df.index[-1].date()}")

    # PHASE 1: grid search over MA combos, aggregated across symbols + folds
    phase1_results = []
    for fast in FAST_OPTIONS:
        for slow in SLOW_OPTIONS:
            if fast >= slow:
                continue
            folds = run_walk_forward(symbol_data, fast, slow)
            agg = aggregate(folds, f"MA{fast}/MA{slow}")
            if agg and agg['total_trades'] >= MIN_TOTAL_TRADES:
                agg['fast'] = fast
                agg['slow'] = slow
                phase1_results.append(agg)

    phase1_sorted = sorted(phase1_results, key=lambda r: (r['consistency_pct'], r['avg_sharpe']), reverse=True)
    print_leaderboard(f"PHASE 1: MA GRID (min {MIN_TOTAL_TRADES} trades, sorted by consistency then Sharpe)", phase1_sorted)

    if not phase1_sorted:
        print("\nNo strategy met the minimum trade threshold. Lower MIN_TOTAL_TRADES or add more history.")
        return

    # PHASE 2: take top 3 by consistency+Sharpe, test SL/TP variants
    top3 = phase1_sorted[:3]
    print(f"\nTop 3 candidates going into Phase 2: {[t['label'] for t in top3]}")

    sl_tp_variants = [
        (None, None, "no SL/TP"),
        (0.05, None, "5% SL"),
        (0.08, None, "8% SL"),
        (0.05, 0.15, "5% SL/15% TP"),
        (0.08, 0.20, "8% SL/20% TP"),
    ]

    phase2_results = []
    for cand in top3:
        fast, slow = cand['fast'], cand['slow']
        for sl, tp, tag in sl_tp_variants:
            folds = run_walk_forward(symbol_data, fast, slow, stop_loss_pct=sl, take_profit_pct=tp)
            agg = aggregate(folds, f"MA{fast}/MA{slow} + {tag}")
            if agg and agg['total_trades'] >= MIN_TOTAL_TRADES:
                phase2_results.append(agg)

    phase2_sorted = sorted(phase2_results, key=lambda r: (r['consistency_pct'], r['avg_sharpe']), reverse=True)
    print_leaderboard("PHASE 2: TOP CANDIDATES x SL/TP VARIANTS", phase2_sorted)

    if phase2_sorted:
        best = phase2_sorted[0]
        print(f"\n=== RECOMMENDED STRATEGY ===")
        print(f"{best['label']}")
        print(f"Consistency: {best['consistency_pct']}% of {best['num_fold_tests']} fold-tests were profitable")
        print(f"Avg Sharpe: {best['avg_sharpe']}, Avg Return: {best['avg_return_pct']}%, "
              f"Avg MaxDD: {best['avg_max_dd_pct']}%, Total Trades: {best['total_trades']}")


if __name__ == "__main__":
    main()