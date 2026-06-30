import anthropic
import base64
import httpx
import os
import json
import re
from datetime import datetime

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """أنت مساعد شخصي ذكي. مهمتك تحليل رسائل المستخدم واستخراج المعلومات منها بشكل منظم.

الـ categories المتاحة:
- مواعيد: أي موعد أو اجتماع أو حدث في وقت محدد
- مهام: أي عمل أو مهمة يجب إنجازها
- مصروفات: أي مبلغ مالي أو مصروف أو دفعة
- تذكيرات: أي تذكير بشيء معين
- ملاحظات: أي معلومة أو ملاحظة عامة

التاريخ والوقت الحالي: {now}

رد دائماً بـ JSON صحيح بالشكل التالي (بدون أي نص إضافي):
{{
  "category": "اسم الكاتيجوري",
  "title": "عنوان قصير وواضح",
  "details": "تفاصيل إضافية إن وجدت",
  "remind_at": "YYYY-MM-DD HH:MM أو null",
  "amount": رقم أو null,
  "currency": "EGP أو USD أو EUR",
  "expense_category": "نوع المصروف مثلاً: طعام، مواصلات، فواتير أو null",
  "summary": "ملخص ما فهمته في جملة واحدة بالعربي"
}}"""


def parse_message(text: str) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    prompt = SYSTEM_PROMPT.format(now=now)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=prompt,
        messages=[{"role": "user", "content": text}]
    )

    raw = response.content[0].text.strip()
    # extract JSON if wrapped in markdown
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group()
    return json.loads(raw)


async def transcribe_voice(file_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    """Transcribe voice using Groq Whisper API (free, no local model needed)."""
    import tempfile, os
    from groq import Groq

    groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        f.write(file_bytes)
        tmp_path = f.name

    try:
        with open(tmp_path, "rb") as audio_file:
            result = groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=("voice.ogg", audio_file, "audio/ogg"),
            )
        return result.text.strip() or "Could not understand audio"
    finally:
        os.unlink(tmp_path)
