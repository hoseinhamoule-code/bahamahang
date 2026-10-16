# نوبت منه آهنگ بزارم 🎧

ربات تلگرامی موسیقایی برای ساخت پلی‌لیست دونفره و گروهی.

## 🚀 راه‌اندازی سریع

```bash
# ۱. کلون ریپو
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# ۲. ساخت محیط مجازی و نصب پیش‌نیازها
python -m venv venv
source venv/bin/activate      # لینوکس/مک
# venv\Scripts\activate       # ویندوز
pip install -r requirements.txt

# ۳. تنظیمات
cp .env.example .env
# فایل .env را باز کنید و BOT_TOKEN و ADMIN_IDS را پر کنید

# ۴. اجرا
python bot.py
```

## 🔑 تنظیمات

| متغیر | توضیح | اجباری |
|---|---|---|
| `BOT_TOKEN` | توکن ربات از @BotFather | ✅ |
| `ADMIN_IDS` | آی‌دی عددی ادمین‌ها (با کاما) | ✅ |
| `PROXY_URL` | آدرس پروکسی (برای اجرا داخل ایران) | ❌ |
| `FORCE_CHANNEL` | کانال اجباری مثل `@mychannel` | ❌ |

> ⚠️ فایل `.env` هرگز کامیت نمی‌شود. توکن را داخل کد قرار ندهید.

## 📋 پنل ادمین

در ربات دستور `/panel` را بفرستید.
