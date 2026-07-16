from config import (
    MAX_POSITION_PERCENT,
    STOP_LOSS_PERCENT,
    TAKE_PROFIT_PERCENT
)



def calculate_position_size(
    account_value,
    price
):

    money = (
        account_value *
        MAX_POSITION_PERCENT
    )

    return int(
        money / price
    )



def check_risk(
    entry_price,
    current_price
):

    change = (
        current_price - entry_price
    ) / entry_price


    if change <= -STOP_LOSS_PERCENT:

        return "STOP_LOSS"


    if change >= TAKE_PROFIT_PERCENT:

        return "TAKE_PROFIT"


    return "HOLD"