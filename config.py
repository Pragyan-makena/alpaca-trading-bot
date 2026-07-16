import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

PAPER_TRADING = True
SYMBOLS = ["SPY", "QQQ", "DIA", "IWM"]

SHORT_WINDOW = 20
LONG_WINDOW = 200

MAX_POSITION_PERCENT = 0.10   # per-symbol max, applied individually below
STOP_LOSS_PERCENT = 0.05
TAKE_PROFIT_PERCENT = 0.10