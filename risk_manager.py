from config import POSITION_PERCENT


def calculate_position_size(account_value, price):
    """Whole shares worth POSITION_PERCENT of equity. The 200-day SMA exit is the risk
    control; fixed stop-loss/take-profit were removed (they cut winners and whipsaw
    a trend filter)."""
    return int(account_value * POSITION_PERCENT / price)
