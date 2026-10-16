# -*- coding: utf-8 -*-
"""🧰 ابزارهای مشترک ربات"""

import html
import logging
import re

import config
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden

log = logging.getLogger("nobateman.utils")

FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

BANNED_TEXT = ("🚫 <b>دسترسی شما به ربات محدود شده است.</b>\n"
               "اگر فکر می‌کنی اشتباهیه، با ادمین ربات در تماس باش.")


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def fa(n) -> str:
    return str(n).translate(FA)


def get_db(context):
    return context.bot_data["db"]


def parse_list(text: str, limit: int) -> list:
    parts = re.split(r"[,،;\n]", text or "")
    out = []
    for p in parts:
        p = p.strip().strip("•-·").strip()
        if p and p not in out:
            out.append(p)
        if len(out) >= limit:
            break
    return out


def match_score(genres_a, singers_a, genres_b, singers_b) -> int:
    g = len(set(genres_a) & set(genres_b))
    s = len(set(singers_a) & set(singers_b))
    return min(100, g * 15 + s * 25)


# ---------- 📣 کانال اجباری ----------
def force_channel(db) -> str:
    """کانال اجباری: اول تنظیم پنل ادمین، بعد پیش‌فرض config"""
    ch = (db.get_setting("force_channel", "") or "").strip()
    if not ch:
        ch = (config.FORCE_CHANNEL or "").strip()
    return ch


def channel_link(ch: str) -> str:
    ch = (ch or "").strip()
    if ch.startswith("https://t.me/"):
        return ch
    if ch.startswith("t.me/"):
        return "https://" + ch
    return "https://t.me/" + ch.lstrip("@")


async def is_channel_member(context, db, user_id) -> bool:
    """🔍 بررسی عضویت کاربر در کانال اجباری (ادمین‌ها همیشه مجازند)"""
    if user_id in config.ADMIN_IDS:
        return True
    ch = force_channel(db)
    if not ch:
        return True
    try:
        m = await context.bot.get_chat_member(ch, user_id)
        return getattr(m, "status", "") in ("member", "administrator", "creator")
    except Exception:
        log.warning("بررسی عضویت کانال ناموفق بود؛ مطمئن شو ربات در %s ادمین است", ch)
        return False


async def notify(context, chat_id: int, text: str, kb=None):
    """📨 ارسال پیام با مدیریت خطا (اگر کاربر ربات را بلاک کرده باشد)"""
    try:
        await context.bot.send_message(
            chat_id, text, parse_mode=ParseMode.HTML,
            reply_markup=kb, disable_web_page_preview=True,
        )
    except (Forbidden, BadRequest):
        pass


async def edit_or_send(update, context, text: str, kb=None):
    """✏️ ویرایش پیام فعلی؛ اگر ممکن نبود پیام جدید می‌فرستد"""
    q = update.callback_query
    msg = getattr(q, "message", None)
    if msg is not None:
        try:
            if msg.text:
                await q.edit_message_text(
                    text, parse_mode=ParseMode.HTML, reply_markup=kb,
                    disable_web_page_preview=True,
                )
                return
            if msg.caption is not None:
                await q.edit_message_caption(
                    caption=text, parse_mode=ParseMode.HTML, reply_markup=kb,
                )
                return
        except BadRequest:
            pass
    await notify(context, q.from_user.id, text, kb)


async def maybe_relay(update, context) -> bool:
    """💬 اگر چت پرو فعال باشد، پیام را برای طرف مقابل می‌فرستد"""
    db = get_db(context)
    uid = update.effective_user.id
    buddy = db.get_active_chat_buddy(uid)
    if not buddy:
        return False
    other = buddy["a_id"] if buddy["b_id"] == uid else buddy["a_id"]
    try:
        await context.bot.copy_message(
            chat_id=other,
            from_chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
        )
        return True
    except Forbidden:
        await notify(context, uid, "💌 پیام نرسید! طرف مقابل ربات رو بلاک کرده 😕")
        return True
    except BadRequest:
        return False