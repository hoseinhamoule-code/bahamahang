# -*- coding: utf-8 -*-
"""🎧 نوبت منه آهنگ بزارم — نقطه شروع ربات (نسخه پرسرعت + پنل ادمین + معرفی + سبک)"""

import asyncio
import logging

from telegram import Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          MessageHandler, filters)
from telegram.request import HTTPXRequest

from config import (API_POOL_SIZE, BOT_TOKEN, CONCURRENT_UPDATES,
                    CONNECT_TIMEOUT, POOL_TIMEOUT, PROXY_URL, READ_TIMEOUT,
                    UPDATES_POOL_SIZE, UPDATES_READ_TIMEOUT, WRITE_TIMEOUT)
from database import Database
import handlers_admin as ha
import handlers_common as hc
import handlers_explore as he
import handlers_group as hg
import handlers_session as hs

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("nobateman")

# 🆕 فقط پیام‌های تازه پردازش می‌شن؛ پیام ویرایش‌شده نادیده گرفته می‌شود تا خطایی رخ ندهد
PM = filters.UpdateType.MESSAGE

# 🎼 آهنگ: هم پیام موزیک (audio) هم فایل صوتی (document با mime صوتی)
AUDIO_ANY = filters.AUDIO | filters.Document.AUDIO

# 🧦 پیشوندهایی که به وابستگی socksio نیاز دارند
SOCKS_SCHEMES = ("socks4://", "socks5://", "socks5h://")


def _check_network_setup():
    """🔍 بررسی توکن و وابستگی پروکسی قبل از اجرا"""
    if not BOT_TOKEN or BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise SystemExit(
            "❌ هنوز توکن ربات را در config.py نگذاشته‌ای!\n"
            "   از @BotFather بگیر و جای PUT_YOUR_BOT_TOKEN_HERE بذار."
        )
    if PROXY_URL and PROXY_URL.lower().startswith(SOCKS_SCHEMES):
        try:
            import socksio  # noqa: F401
        except ImportError:
            raise SystemExit(
                "❌ برای پروکسی SOCKS باید پکیج socksio نصب باشد:\n"
                '   pip install "python-telegram-bot[socks]"\n'
                "   (یا به‌جای SOCKS از پروکسی HTTP استفاده کن: http://...)"
            )


def _make_api_request() -> HTTPXRequest:
    """🚀 لایه شبکه ارسال پیام‌ها — با استخر اتصال بزرگ برای پردازش همزمان"""
    return HTTPXRequest(
        connection_pool_size=API_POOL_SIZE,
        proxy=PROXY_URL or None,
        connect_timeout=CONNECT_TIMEOUT,
        read_timeout=READ_TIMEOUT,
        write_timeout=WRITE_TIMEOUT,
        pool_timeout=POOL_TIMEOUT,
    )


def _make_updates_request() -> HTTPXRequest:
    """📡 لایه شبکه دریافت آپدیت‌ها — تایم‌اوت مخصوص long-polling"""
    return HTTPXRequest(
        connection_pool_size=UPDATES_POOL_SIZE,
        proxy=PROXY_URL or None,
        connect_timeout=CONNECT_TIMEOUT,
        read_timeout=UPDATES_READ_TIMEOUT,
        write_timeout=WRITE_TIMEOUT,
        pool_timeout=POOL_TIMEOUT,
    )


async def on_error(update, context):
    log.error("خطا در پردازش آپدیت", exc_info=context.error)


def main():
    _check_network_setup()

    # 🔁 در پایتون‌های ۳.۱۲ به بالا، event loop خودکار ساخته نمی‌شود؛
    # پس خودمان یکی می‌سازیم تا run_polling بدون خطا اجرا شود
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    db = Database()

    # 🌐 اتصال به تلگرام: دو لایه شبکه جدا + پردازش همزمان آپدیت‌ها
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(_make_api_request())
        .get_updates_request(_make_updates_request())
        .concurrent_updates(CONCURRENT_UPDATES)
        .build()
    )
    app.bot_data["db"] = db

    if PROXY_URL:
        log.info("🌐 اتصال از طریق پروکسی فعال شد: %s", PROXY_URL)
    else:
        log.info("🌐 اتصال مستقیم (بدون پروکسی)")
    log.info("⚡ پردازش همزمان %s آپدیت فعال است", CONCURRENT_UPDATES)

    # ---------- دستورهای خصوصی ----------
    app.add_handler(CommandHandler("start", hc.cmd_start_private, filters=filters.ChatType.PRIVATE), group=0)
    app.add_handler(CommandHandler("help", hc.cmd_help, filters=filters.ChatType.PRIVATE), group=0)
    app.add_handler(CommandHandler("done", hc.cmd_done, filters=filters.ChatType.PRIVATE), group=0)
    app.add_handler(CommandHandler("chatoff", hc.cmd_chatoff, filters=filters.ChatType.PRIVATE), group=0)
    app.add_handler(CommandHandler("panel", ha.cmd_panel, filters=filters.ChatType.PRIVATE), group=0)
    app.add_handler(CommandHandler("addpro", hc.cmd_addpro), group=0)
    app.add_handler(CommandHandler("rmpro", hc.cmd_rmpro), group=0)
    app.add_handler(CommandHandler("stats", hc.cmd_stats), group=0)

    # ---------- گروه ----------
    app.add_handler(CommandHandler(["start", "music"], hg.cmd_group_start, filters=filters.ChatType.GROUPS), group=0)
    app.add_handler(CommandHandler("stop", hg.cmd_group_stop, filters=filters.ChatType.GROUPS), group=0)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & PM & AUDIO_ANY, hg.on_group_audio), group=0)

    # ---------- کال‌بک‌ها ----------
    app.add_handler(CallbackQueryHandler(hc.on_menu_cb, pattern=r"^menu:"), group=0)
    app.add_handler(CallbackQueryHandler(hc.on_ref_cb, pattern=r"^ref:"), group=0)
    app.add_handler(CallbackQueryHandler(hc.on_profile_cb, pattern=r"^(profile:|genre:|genres:)"), group=0)
    app.add_handler(CallbackQueryHandler(hs.on_player_cb, pattern=r"^pl:(next|prev|list|stop|restart):\d+$"), group=0)
    app.add_handler(CallbackQueryHandler(hs.on_personal_cb, pattern=r"^per:"), group=0)
    app.add_handler(CallbackQueryHandler(hs.on_popular_cb, pattern=r"^pop:"), group=0)
    app.add_handler(CallbackQueryHandler(hs.on_blist_cb, pattern=r"^(blist:|bl:)"), group=0)
    app.add_handler(CallbackQueryHandler(he.on_explore_cb, pattern=r"^ex:"), group=0)
    app.add_handler(CallbackQueryHandler(he.on_buddy_cb, pattern=r"^(buddy:|bsize:|bgenre:)"), group=0)
    app.add_handler(CallbackQueryHandler(hg.on_group_cb, pattern=r"^g:"), group=0)
    app.add_handler(CallbackQueryHandler(ha.on_admin_cb, pattern=r"^ad:"), group=0)
    app.add_handler(CallbackQueryHandler(ha.on_broadcast_cb, pattern=r"^bc:"), group=0)

    # ---------- پیوی: آهنگ و عکس ----------
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & PM & AUDIO_ANY, hs.on_private_audio), group=0)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & PM & (filters.PHOTO | filters.VOICE), hc.on_private_photo), group=0)

    # ---------- پیوی: متن‌ها (گروه ۱ — بعد از بقیه اجرا می‌شود) ----------
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & PM & filters.TEXT & ~filters.COMMAND, hc.on_private_text), group=1)

    app.add_error_handler(on_error)
    log.info("🎧 ربات «نوبت منه آهنگ بزارم» روشن شد!")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()