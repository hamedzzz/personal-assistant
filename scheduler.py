import asyncio
import os
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

import database as db

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CATEGORY_EMOJI = {
    "مواعيد": "📅",
    "مهام": "✅",
    "مصروفات": "💰",
    "تذكيرات": "🔔",
    "ملاحظات": "📝",
}


async def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        })


async def check_reminders():
    pending = db.get_pending_reminders()
    for item in pending:
        emoji = CATEGORY_EMOJI.get(item["category"], "🔔")
        msg = f"{emoji} *تذكير!*\n\n*{item['title']}*"
        if item["details"]:
            msg += f"\n_{item['details']}_"
        if item["amount"]:
            msg += f"\n💵 {item['amount']} {item['currency']}"
        msg += f"\n\n_ID: {item['id']} — /done {item['id']} لما تخلص_"
        await send_telegram(msg)
        db.mark_reminded(item["id"])


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_reminders, "interval", minutes=1)
    scheduler.start()
    return scheduler
