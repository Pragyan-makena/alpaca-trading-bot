import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

PAPER_TRADING = True  # never flip this until months of paper results

SYMBOLS = ["SPY", "QQQ", "DIA", "IWM"]

# Trend filter: hold when price is above its 200-day SMA, flat when below.
SMA_WINDOW = 200
# Hysteresis band: enter only if price > SMA*(1+BAND), exit only if price < SMA*(1-BAND).
# Inside the band, do nothing. Cuts whipsaw around the average.
BAND = 0.01

# Equal weight across symbols, no leverage (4 x 24% = 96% max invested).
POSITION_PERCENT = 0.24
