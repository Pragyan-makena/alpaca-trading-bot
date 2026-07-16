# Alpaca Paper Trading Bot

## Setup

Install packages:

pip install -r requirements.txt


Create environment variables:

ALPACA_API_KEY=your_paper_key

ALPACA_SECRET_KEY=your_paper_secret


## Run

python main.py


## Strategy

BUY:
20-day moving average > 50-day moving average

SELL:
20-day moving average < 50-day moving average


## Safety

- Paper trading only
- No live trading
- Position size limits
- Logging enabled