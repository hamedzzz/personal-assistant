# إعداد المساعد الشخصي الذكي

## الخطوات

### 1. إنشاء Telegram Bot
1. افتح Telegram وكلم [@BotFather](https://t.me/BotFather)
2. ابعت `/newbot` واتبع التعليمات
3. احتفظ بـ **Bot Token**
4. عشان تعرف Chat ID بتاعك: كلم [@userinfobot](https://t.me/userinfobot)

### 2. إعداد ملف البيئة
```bash
cp .env.example .env
```
افتح `.env` وحط:
```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHI...
TELEGRAM_CHAT_ID=123456789
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. تثبيت المكتبات
```bash
cd C:\Users\accah\personal-assistant
pip install -r requirements.txt
```

### 4. تشغيل النظام
```bash
python main.py
```

سيفتح:
- 🤖 Telegram Bot — يستقبل رسائلك
- 🌐 Web Dashboard — http://localhost:8765
- ⏰ Scheduler — يراقب التذكيرات كل دقيقة

---

## كيف تستخدمه؟

### على Telegram ابعت مثلاً:
| الرسالة | ما سيحدث |
|---|---|
| "عندي اجتماع مع العميل بكرة الساعة 3" | 📅 موعد + تذكير |
| "دفعت 350 جنيه غداء" | 💰 مصروف - طعام |
| "فكرني أكلم محمد يوم الخميس الصبح" | 🔔 تذكير |
| "مهمة: مراجعة العقد قبل نهاية الأسبوع" | ✅ مهمة |
| Voice note بأي من ده | نفس الشيء 🎤 |

### أوامر البوت:
- `/list` — كل العناصر
- `/list مواعيد` — مواعيد فقط
- `/expenses` — ملخص المصروفات
- `/done 5` — إنهاء العنصر رقم 5

### Web Dashboard:
- فلتر بالكاتيجوري
- بحث نصي
- رسم بياني للمصروفات
- تحديث تلقائي كل 30 ثانية
