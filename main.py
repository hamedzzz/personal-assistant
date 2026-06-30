"""Entry point — runs Telegram bot + reminder scheduler + web API + ngrok tunnel."""
import asyncio
import threading
import time
import os
import sys
from dotenv import load_dotenv

# Fix Unicode output on Windows background processes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

import database as db
from api import app as flask_app

PORT = int(os.environ.get("PORT", 8765))


def run_web():
    flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


def start_ngrok():
    try:
        from pyngrok import ngrok, conf

        token = os.environ.get("NGROK_AUTH_TOKEN")
        if token:
            conf.get_default().auth_token = token

        ngrok_path = os.environ.get("NGROK_PATH")
        if ngrok_path:
            conf.get_default().ngrok_path = ngrok_path

        tunnel = ngrok.connect(PORT, "http")
        url = tunnel.public_url
        if url.startswith("http://"):
            url = "https://" + url[7:]
        return url
    except Exception as e:
        print(f"ngrok unavailable: {e}")
        return None


async def notify_url(url: str):
    import httpx
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    msg = f"Dashboard ready!\n\n{url}"
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg},
        )


def main():
    db.init_db()

    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    time.sleep(1)
    print(f"Web dashboard: http://localhost:{PORT}")

    # Skip ngrok on Railway (it has its own public URL)
    on_railway = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RAILWAY_SERVICE_NAME")
    if not on_railway:
        public_url = start_ngrok()
        if public_url:
            print(f"Public URL: {public_url}")
            asyncio.run(notify_url(public_url))

    from bot import run_bot
    run_bot()


if __name__ == "__main__":
    main()
