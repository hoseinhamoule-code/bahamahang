# -*- coding: utf-8 -*-
"""🛠 پنل ادمین — مدیریت کاربران، پیام همگانی و کانال اجباری"""

import asyncio
import json

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from keyboards import (admin_back_kb, admin_channel_kb, admin_panel_kb,
                       admin_user_kb, admin_users_kb, broadcast_confirm_kb)
from utils import (channel_link, edit_or_send, esc, fa, force_channel, get_db,
                   notify)

PER_PAGE = 10


def _is_admin(uid) -> bool:
    return uid in ADMIN_IDS


def _panel_text(db) -> str:
    s = db.admin_stats()
    return (
        "🛠 <b>پنل ادمین</b>\n\n"
        f"👥 کاربران: <b>{fa(s['users'])}</b>\n"
        f"💎 پرو: {fa(s['pro'])} | 🚫 بن: {fa(s['banned'])}\n"
        f"🎧 جلسات پلی‌لیست: {fa(s['sessions'])} | 🎵 آهنگ‌ها: {fa(s['tracks'])}\n"
        f"💚 مچ‌ها: {fa(s['buddies'])} | ❤️ لایک‌ها: {fa(s['likes'])}\n\n"
        "👇 یک بخش رو انتخاب کن:"
    )


async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        return
    db = get_db(context)
    context.user_data.pop("admin_flow", None)
    await update.message.reply_html(
        _panel_text(db),
        reply_markup=admin_panel_kb(bool(force_channel(db))),
        disable_web_page_preview=True,
    )


def _user_label(u) -> str:
    name = (u["display_name"] or u["tg_name"] or str(u["user_id"]))[:18]
    marks = ("💎" if u["is_pro"] else "") + ("🚫" if u["banned"] else "")
    return f"👤 {marks}{esc(name)}"


async def _users_view(update, context, page: int):
    db = get_db(context)
    total = db.count_users()
    pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = max(0, min(page, pages - 1))
    context.user_data["ad_page"] = page
    rows = db.all_users(page, PER_PAGE)
    lines = [f"👥 <b>کاربران</b> — مجموع: <b>{fa(total)}</b>", ""]
    if rows:
        for u in rows:
            lines.append(f"{_user_label(u)} | 🆔 <code>{u['user_id']}</code>")
    else:
        lines.append("هنوز کاربری ثبت نشده!")
    lines.append("")
    lines.append("👇 روی هر کاربر بزن تا مدیریتش کنی:")
    await edit_or_send(update, context, "\n".join(lines),
                       admin_users_kb(rows, page, pages))


def _user_detail_text(db, u) -> str:
    genres = ", ".join(json.loads(u["genres"] or "[]")) or "—"
    singers = ", ".join(json.loads(u["singers"] or "[]")) or "—"
    ntracks = len(db.personal_tracks(u["user_id"]))
    pro = "💎 پرو" if u["is_pro"] else "معمولی"
    ban = "🚫 بن شده" if u["banned"] else "✅ فعال"
    return (
        f"{_user_label(u)}\n"
        f"🆔 <code>{u['user_id']}</code>\n"
        f"🔗 یوزرنیم: @{u['username'] or 'ندارد'}\n"
        f"🏙 شهر: {esc(u['city']) or '—'} | 🎂 سن: {fa(u['age'])}\n"
        f"🎼 سبک‌ها: {esc(genres)}\n"
        f"🎤 خواننده‌ها: {esc(singers)}\n\n"
        f"💎 وضعیت: {pro} | {ban}\n"
        f"🧭 بازدید اکسپلور: {fa(u['explore_views'])} (بازشده: {fa(u['explore_unlocked'])})\n"
        f"🎧 آهنگ‌های شخصی: {fa(ntracks)}\n"
        f"📅 عضویت: {esc(u['created_at'])}"
    )


async def _channel_view(update, context, db):
    ch = force_channel(db)
    if ch:
        text = (
            "📣 <b>کانال اجباری</b>\n\n"
            f"کانال فعلی: <code>{esc(ch)}</code>\n"
            f"🔗 لینک: {channel_link(ch)}\n\n"
            "⚠️ ربات باید در این کانال <b>ادمین</b> باشد تا بتواند عضویت کاربران را بررسی کند.\n"
            "📌 با هر تأیید عضویت، ۵ نفر بعدی اکسپلور برای کاربر باز می‌شود.\n"
            "👑 ادمین‌ها همیشه بدون عضویت هم می‌توانند اکسپلور را ببینند."
        )
    else:
        text = (
            "📣 <b>کانال اجباری</b>\n\n"
            "هیچ کانالی تنظیم نشده — دیوار عضویت غیرفعال است و همه می‌توانند "
            "بدون محدودیت اکسپلور را ببینند.\n\n"
            "✏️ برای فعال‌سازی، آیدی عمومی کانال (مثل @mychannel) را تنظیم کن."
        )
    await edit_or_send(update, context, text, admin_channel_kb(bool(ch)))


def _normalize_channel(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("https://t.me/"):
        t = "@" + t[len("https://t.me/"):].strip("/")
    elif t.startswith("t.me/"):
        t = "@" + t[len("t.me/"):].strip("/")
    if not t or t.lstrip("-").isdigit():
        return ""  # فقط آیدی عمومی (@username) پذیرفته می‌شود تا لینک ساخته شود
    if not t.startswith("@"):
        t = "@" + t.lstrip("@")
    if len(t) < 5:
        return ""
    return t


async def on_admin_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = get_db(context)
    uid = q.from_user.id
    if not _is_admin(uid):
        await q.answer("فقط ادمین! 🙅", show_alert=True)
        return
    parts = q.data.split(":")
    route = parts[1]

    if route == "nop":
        await q.answer()
        return

    if route == "panel":
        await q.answer()
        context.user_data.pop("admin_flow", None)
        await edit_or_send(update, context, _panel_text(db),
                           admin_panel_kb(bool(force_channel(db))))
        return

    if route == "stats":
        await q.answer()
        s = db.admin_stats()
        text = (
            "📊 <b>آمار کامل ربات</b>\n\n"
            f"👥 کاربران: <b>{fa(s['users'])}</b>\n"
            f"💎 پرو: {fa(s['pro'])}\n"
            f"🚫 بن: {fa(s['banned'])}\n"
            f"🎧 جلسات پلی‌لیست: {fa(s['sessions'])}\n"
            f"🎵 آهنگ‌های مشترک: {fa(s['tracks'])}\n"
            f"💚 مچ‌ها: {fa(s['buddies'])}\n"
            f"❤️ لایک پلی‌لیست‌ها: {fa(s['likes'])}"
        )
        await edit_or_send(update, context, text, admin_back_kb())
        return

    if route == "users":
        await q.answer()
        try:
            page = int(parts[2])
        except (IndexError, ValueError):
            page = 0
        await _users_view(update, context, page)
        return

    if route in ("user", "pro", "ban", "resetexp", "dm"):
        try:
            t = int(parts[2])
        except (IndexError, ValueError):
            await q.answer("دستور نامعتبره 🤔", show_alert=True)
            return
        u = db.get_user(t)
        if not u:
            await q.answer("کاربر پیدا نشد 🤷", show_alert=True)
            return

        if route == "user":
            await q.answer()
            await edit_or_send(update, context, _user_detail_text(db, u),
                               admin_user_kb(t, bool(u["is_pro"]), bool(u["banned"])))
            return

        if route == "pro":
            newval = 0 if u["is_pro"] else 1
            db.set_user_fields(t, is_pro=newval)
            await q.answer("💎 پرو شد" if newval else "▫️ پرو حذف شد")
            await notify(context, t,
                         "🎉 تبریک! عضو نسخه <b>پرو</b> شدی؛ حالا بعد از مچ می‌تونی چت کنی! 💬"
                         if newval else "▫️ عضویت پروت حذف شد.")
            u = db.get_user(t)
            await edit_or_send(update, context, _user_detail_text(db, u),
                               admin_user_kb(t, bool(u["is_pro"]), bool(u["banned"])))
            return

        if route == "ban":
            newval = 0 if u["banned"] else 1
            db.set_user_fields(t, banned=newval)
            await q.answer("🚫 بن شد" if newval else "✅ آزاد شد")
            await notify(context, t,
                         "🚫 <b>دسترسی‌ات به ربات محدود شد.</b>"
                         if newval else "✅ <b>آزاد شدی!</b> دوباره می‌تونی از ربات استفاده کنی 🎧")
            u = db.get_user(t)
            await edit_or_send(update, context, _user_detail_text(db, u),
                               admin_user_kb(t, bool(u["is_pro"]), bool(u["banned"])))
            return

        if route == "resetexp":
            db.reset_explore_views(t)
            await q.answer("🔄 بازدیدهای اکسپلور ریست شد")
            u = db.get_user(t)
            await edit_or_send(update, context, _user_detail_text(db, u),
                               admin_user_kb(t, bool(u["is_pro"]), bool(u["banned"])))
            return

        if route == "dm":
            context.user_data["admin_flow"] = ("dm", t)
            await q.answer("📩")
            await notify(context, uid,
                         f"📩 متن پیام به کاربر <code>{t}</code> رو بفرست:\n"
                         "(برای لغو بنویس: لغو)")
            return

    if route == "bcast":
        context.user_data["admin_flow"] = ("broadcast",)
        await q.answer("📢")
        await notify(context, uid,
                     "📢 متن پیام همگانی رو بفرست:\n"
                     "برای همه کاربران ارسال می‌شه (قبل از ارسال، پیش‌نمایش می‌بینی).\n"
                     "(برای لغو بنویس: لغو)")
        return

    if route == "chan":
        await q.answer()
        await _channel_view(update, context, db)
        return

    if route == "chanset":
        context.user_data["admin_flow"] = ("channel",)
        await q.answer("✏️")
        await notify(context, uid,
                     "📣 آیدی عمومی کانال رو بفرست (مثل @mychannel):\n"
                     "⚠️ ربات باید در کانال ادمین باشه تا بتونه عضویت رو چک کنه.\n"
                     "(برای لغو بنویس: لغو)")
        return

    if route == "chandel":
        db.set_setting("force_channel", "")
        await q.answer("🗑 کانال حذف شد")
        await _channel_view(update, context, db)
        return

    await q.answer()


async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """اگر پیام متنی متعلق به جریان ادمین بود، پردازش می‌کند و True برمی‌گرداند"""
    flow = context.user_data.get("admin_flow")
    if not flow:
        return False
    uid = update.effective_user.id
    if not _is_admin(uid):
        context.user_data.pop("admin_flow", None)
        return False
    db = get_db(context)
    text = (update.message.text or "").strip()
    if text in ("/cancel", "/done", "لغو", "کنسل"):
        context.user_data.pop("admin_flow", None)
        await update.message.reply_text("✅ لغو شد.")
        return True
    kind = flow[0]

    if kind == "broadcast":
        context.user_data.pop("admin_flow", None)
        context.user_data["bc_text"] = text
        await update.message.reply_html(
            "📢 <b>پیش‌نمایش پیام همگانی:</b>\n\n" + esc(text) +
            f"\n\n👥 این پیام برای <b>{fa(db.count_users())}</b> کاربر ارسال می‌شه. مطمئنی؟",
            reply_markup=broadcast_confirm_kb(),
        )
        return True

    if kind == "dm":
        target = flow[1]
        context.user_data.pop("admin_flow", None)
        try:
            await context.bot.send_message(
                target, f"📩 <b>پیام از ادمین ربات:</b>\n\n{esc(text)}",
                parse_mode=ParseMode.HTML,
            )
            await update.message.reply_html("✅ پیام ارسال شد!")
        except (Forbidden, BadRequest):
            await update.message.reply_html(
                "❌ ارسال نشد؛ کاربر ربات رو بلاک کرده یا استارت نزده."
            )
        return True

    if kind == "channel":
        context.user_data.pop("admin_flow", None)
        ch = _normalize_channel(text)
        if not ch:
            await update.message.reply_text(
                "❌ آیدی معتبر نیست؛ مثل @mychannel بفرست (فقط آیدی عمومی)."
            )
            return True
        db.set_setting("force_channel", ch)
        await update.message.reply_html(
            f"✅ کانال اجباری تنظیم شد: <code>{esc(ch)}</code>\n"
            "⚠️ یادت باشه ربات باید توی این کانال ادمین باشه!",
            reply_markup=admin_channel_kb(True),
        )
        return True

    return False


async def on_broadcast_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = get_db(context)
    uid = q.from_user.id
    if not _is_admin(uid):
        await q.answer("فقط ادمین! 🙅", show_alert=True)
        return
    if q.data == "bc:no":
        context.user_data.pop("bc_text", None)
        await q.answer("لغو شد ❌")
        try:
            if q.message:
                await q.edit_message_text("📢 ارسال همگانی لغو شد.")
        except Exception:
            pass
        return
    text = context.user_data.get("bc_text")
    if not text:
        await q.answer("پیامی برای ارسال نیست 🤷", show_alert=True)
        return
    await q.answer("در حال ارسال... ⏳")
    ids = db.all_user_ids()
    sent = fail = 0
    for t in ids:
        try:
            await context.bot.send_message(t, esc(text), parse_mode=ParseMode.HTML)
            sent += 1
        except (Forbidden, BadRequest):
            fail += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    context.user_data.pop("bc_text", None)
    try:
        if q.message:
            await q.edit_message_text(
                "📢 <b>ارسال همگانی تمام شد!</b>\n\n"
                f"✅ رسید: {fa(sent)}\n❌ نرسید: {fa(fail)}",
                parse_mode=ParseMode.HTML,
            )
    except Exception:
        pass