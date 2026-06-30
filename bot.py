import asyncio
import os
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from dotenv import load_dotenv

import database as db
import ai_processor as ai

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", "0"))


def is_allowed(update: Update) -> bool:
    if ALLOWED_CHAT_ID == 0:
        return True
    return update.effective_chat.id == ALLOWED_CHAT_ID


CATEGORY_EMOJI = {
    "مواعيد": "📅",
    "مهام": "✅",
    "مصروفات": "💰",
    "تذكيرات": "🔔",
    "ملاحظات": "📝",
}


async def process_text(update: Update, text: str):
    await update.message.reply_text("⏳ بفكر...")
    try:
        parsed = ai.parse_message(text)
        item_id = db.insert_item(
            category=parsed.get("category", "ملاحظات"),
            title=parsed["title"],
            details=parsed.get("details"),
            amount=parsed.get("amount"),
            currency=parsed.get("currency", "EGP"),
            remind_at=parsed.get("remind_at"),
            raw_message=text,
            expense_category=parsed.get("expense_category"),
        )
        cat = parsed.get("category", "ملاحظات")
        emoji = CATEGORY_EMOJI.get(cat, "📌")
        reply = f"{emoji} *{cat}* — تم الحفظ!\n\n"
        reply += f"*{parsed['title']}*\n"
        if parsed.get("details"):
            reply += f"_{parsed['details']}_\n"
        if parsed.get("amount"):
            reply += f"\n💵 {parsed['amount']} {parsed.get('currency','EGP')}"
        if parsed.get("remind_at"):
            reply += f"\n⏰ هفكرك: {parsed['remind_at']}"
        reply += f"\n\n💬 _{parsed.get('summary','')}_"
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ حصل خطأ: {e}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await process_text(update, update.message.text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text("🎤 بسمع الصوت...")
    try:
        voice = update.message.voice or update.message.audio
        file = await context.bot.get_file(voice.file_id)
        async with httpx.AsyncClient() as client:
            resp = await client.get(file.file_path)
        transcribed = await ai.transcribe_voice(resp.content, "audio/ogg")
        await update.message.reply_text(f"📝 فهمت: _{transcribed}_", parse_mode="Markdown")
        await process_text(update, transcribed)
    except Exception as e:
        await update.message.reply_text(f"❌ مقدرتش أفهم الصوت: {e}")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    args = context.args
    category = args[0] if args else None
    items = db.get_items(category=category, done=False)
    if not items:
        await update.message.reply_text("مفيش حاجة محفوظة دلوقتي 🎉")
        return
    text = f"📋 *قائمتك* ({len(items)} عنصر):\n\n"
    for item in items[:15]:
        emoji = CATEGORY_EMOJI.get(item["category"], "📌")
        text += f"{emoji} *{item['title']}*"
        if item["remind_at"]:
            text += f" — ⏰ {item['remind_at']}"
        if item["amount"]:
            text += f" — 💵 {item['amount']} {item['currency']}"
        text += f"\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    summary = db.get_expense_summary()
    if not summary:
        await update.message.reply_text("مفيش مصروفات مسجلة 💸")
        return
    text = "💰 *ملخص المصروفات:*\n\n"
    total = 0
    for row in summary:
        text += f"• {row['expense_category']}: *{row['total']} {row['currency']}*\n"
        total += row["total"]
    text += f"\n🔢 *الإجمالي: {total:.2f}*"
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update) or not context.args:
        return
    item_id = int(context.args[0])
    db.mark_done(item_id)
    await update.message.reply_text(f"✅ تم إنهاء العنصر #{item_id}")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """🤖 *المساعد الشخصي الذكي*

ابعتلي أي رسالة أو voice note وهفهمها وأحطها في الكاتيجوري الصح!

*أمثلة:*
• "عندي اجتماع بكرة الساعة 3 العصر"
• "دفعت 250 جنيه أكل"
• "فكرني أكلم محمد الجمعة"
• "مهمة: مراجعة العقد قبل نهاية الأسبوع"

*أوامر:*
/list — كل العناصر
/list مواعيد — فلتر بكاتيجوري
/expenses — ملخص المصروفات
/done [id] — تمام خلصت
/help — المساعدة"""
    await update.message.reply_text(text, parse_mode="Markdown")


def run_bot():
    db.init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_help))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("expenses", cmd_expenses))
    app.add_handler(CommandHandler("done", cmd_done))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    print("🤖 البوت شغال...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_bot()
