import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def send_discord_message(message):
    if not WEBHOOK_URL:
        return  # no webhook configured, skip silently

    try:
        requests.post(
            WEBHOOK_URL,
            json={"content": message},
            timeout=10
        )
    except Exception as e:
        print(f"Discord notification failed: {e}")