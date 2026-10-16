# -*- coding: utf-8 -*-
"""⚙️ تنظیمات کلی ربات «نوبت منه آهنگ بزارم» 🎧

امنیت: هیچ مقدار حساسی (توکن، آی‌دی) داخل کد نوشته نمی‌شود.
همه‌ی مقادیر از فایل `.env` یا متغیرهای محیطی خوانده می‌شوند.
فایل `.env.example` را به `.env` تغییر نام دهید و مقادیر را پر کنید.
"""

import os

# اگر python-dotenv نصب است، فایل .env به‌صورت خودکار خوانده می‌شود
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # بدون dotenv هم کار می‌کند؛ مقادیر را از متغیر محیطی می‌خواند


def _env_int(name: str, default: int) -> int:
    """خواندن یک عدد صحیح از متغیر محیطی با مقدار پیش‌فرض."""
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# 🔑 توکن ربات (اجباری) — از @BotFather بگیرید و فقط در .env بگذارید
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise RuntimeError(
        "❌ توکن ربات پیدا نشد!\n"
        "   فایل .env.example را به .env تغییر نام دهید و BOT_TOKEN را پر کنید."
    )

# 👑 آی‌دی عددی ادمین‌ها — با کاما جدا کنید، مثال: ADMIN_IDS=111613881,222333444
ADMIN_IDS = [
    _env_int(x.strip(), 0)
    for x in os.environ.get("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
]

# 🌐 ---------- پروکسی (برای اجرا در ایران) ----------
# 🔸 روی «سرور خارج از ایران» خالی بگذار (اتصال مستقیم و سریع).
# 🔸 روی «سیستم شخصی داخل ایران» آدرس پروکسی کلاینت‌تان را در .env بگذار:
#     PROXY_URL=socks5h://127.0.0.1:10808   یا   http://127.0.0.1:7890
PROXY_URL = os.environ.get("PROXY_URL", "")

# ⏱ تایم‌اوت‌ها (ثانیه)
CONNECT_TIMEOUT = 15.0        # ⚡ کوتاه تا اگر پروکسی هنگ کرد، سریع دوباره تلاش کند
READ_TIMEOUT = 30.0
WRITE_TIMEOUT = 120.0         # ⏳ آپلود/دانلود آهنگ روی پروکسی کند ممکن است طول بکشد
POOL_TIMEOUT = 10.0

# 🚀 اتصال‌های موازی — برای سرعت بالا
API_POOL_SIZE = _env_int("API_POOL_SIZE", 64)          # 🌐 اتصال‌های همزمان ارسال
UPDATES_POOL_SIZE = _env_int("UPDATES_POOL_SIZE", 4)   # 📥 اتصال‌های دریافت آپدیت‌ها
UPDATES_READ_TIMEOUT = 20.0   # 📡 باید بیشتر از تایم‌اوت long-polling باشد

# ⚙️ پردازش همزمان آپدیت‌ها — مهم‌ترین عامل سرعت
CONCURRENT_UPDATES = _env_int("CONCURRENT_UPDATES", 64)

# 🧭 ---------- اکسپلور ----------
EXPLORE_FREE_VIEWS = 10       # 🎯 تعداد نفراتی که هر کاربر رایگان می‌بیند
EXPLORE_CHANNEL_BATCH = 5     # 📣 با عضویت در کانال، هر بار ۵ نفر بعدی باز می‌شود

# 📣 کانال اجباری (پیش‌فرض — از پنل ادمین /panel هم قابل تنظیم است و تنظیم پنل بر این مقدم است)
FORCE_CHANNEL = os.environ.get("FORCE_CHANNEL", "")   # مثلا "@mychannel" — خالی یعنی غیرفعال

# 🎵 پلی‌لیست‌های دونفره: اندازه پلی‌لیست → تعداد آهنگ برای هر نفر
PLAYLIST_MODES = {2: 1, 6: 3, 10: 5}

# 👥 حالت گروهی
GROUP_MAX_MEMBERS = 5      # حداکثر نفرات
GROUP_TRACKS_PER_USER = 2  # سهمیه آهنگ هر نفر

# 👤 پروفایل
MAX_GENRES = 3
MAX_SINGERS = 3

# 🎼 لیست ۲۰ سبک موسیقی
GENRES = [
    "پاپ 🎤", "سنتی 🎻", "راک 🎸", "رپ و هیپ‌هاپ 🎙", "کلاسیک 🎹",
    "جاز 🎷", "الکترونیک و دنس 🪩", "بلوز 🎺", "متال 🤘", "آر اند بی 🎛",
    "سول 🎚", "فولک 🪕", "ساندتراک فیلم 🎬", "لو-فای 🌙", "چیل‌اوت و امبینت 🌊",
    "کانتری 🤠", "رگی 🌴", "پانک ⚡", "ایندی 🌌", "لاتین 💃",
]

# 💾 مسیر فایل دیتابیس
DB_PATH = os.environ.get("DB_PATH", "nobateman.db")

# 🏷 نام نمایشی ربات
BOT_NAME = "نوبت منه آهنگ بزارم 🎧"
