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


_whisper_model = None

def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        print("⏳ بيحمل موديل Whisper (أول مرة بس)...")
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        print("✅ موديل Whisper جاهز")
    return _whisper_model


def _do_transcribe(file_bytes: bytes) -> str:
    import tempfile, os, subprocess

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        f.write(file_bytes)
        ogg_path = f.name

    wav_path = ogg_path.replace(".ogg", ".wav")
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run(
            [ffmpeg_exe, "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path],
            check=True, capture_output=True
        )
        model = _get_whisper()
        segments, _ = model.transcribe(wav_path)  # auto-detect language
        text = " ".join(s.text for s in segments).strip()
        return text or "مقدرتش أفهم الصوت"
    finally:
        for p in (ogg_path, wav_path):
            if os.path.exists(p):
                os.unlink(p)


async def transcribe_voice(file_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    """Run blocking Whisper transcription in a thread so it doesn't block the bot."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _do_transcribe, file_bytes)
