import logging


logging.basicConfig(
    filename="trading_bot.log",
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)


def log(message):

    print(message)

    logging.info(message)