import os
import database as db

CATEGORY_EMOJI = {
    "مواعيد": "📅",
    "مهام": "✅",
    "مصروفات": "💰",
    "تذكيرات": "🔔",
    "ملاحظات": "📝",
}

# Timezone offset in hours (Egypt = UTC+3)
TZ_OFFSET = int(os.environ.get("TZ_OFFSET", "3"))


async def check_reminders(context):
    """Called every minute by the bot's job queue."""
    bot = context.bot
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    pending = db.get_pending_reminders(tz_offset=TZ_OFFSET)
    for item in pending:
        emoji = CATEGORY_EMOJI.get(item["category"], "🔔")
        msg = f"{emoji} *Reminder!*\n\n*{item['title']}*"
        if item["details"]:
            msg += f"\n_{item['details']}_"
        if item["amount"]:
            msg += f"\n💵 {item['amount']} {item['currency']}"
        msg += f"\n\n/done {item['id']} when finished"
        await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        db.mark_reminded(item["id"])
