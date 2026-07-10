#!/usr/bin/env python3
"""
Simple Telegram Update Sender for Wisconsin Overlay Map
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")  # Add your bot token to .env if needed
CHAT_ID = 6037203711

def send_telegram_message(message: str):
    """Send a message to the user's Telegram bot."""
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not set in .env. Message not sent.")
        print(f"Would have sent: {message}")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("Telegram message sent successfully.")
        else:
            print(f"Failed to send message: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

if __name__ == "__main__":
    send_telegram_message("Wisconsin Overlay Map project update system is now active.")