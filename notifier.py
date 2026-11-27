import os
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
NTFY_TOPIC = os.getenv("NTFY_TOPIC")


def send_discord_message(message):
    if DISCORD_WEBHOOK_URL:
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
        except Exception as e:
            print(f"Discord notification failed: {e}")
    if NTFY_TOPIC:
        try:
            requests.post(
                f"https://ntfy.sh/{NTFY_TOPIC}",
                data=message.encode("utf-8"),
                headers={"Title": "Trading bot"},
                timeout=10,
            )
        except Exception as e:
            print(f"ntfy notification failed: {e}")
