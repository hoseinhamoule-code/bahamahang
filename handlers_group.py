# -*- coding: utf-8 -*-
"""👥 حالت گروهی ربات — تا ۵ نفر با هم پلی‌لیست می‌سازند"""

from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import GROUP_MAX_MEMBERS, GROUP_TRACKS_PER_USER
from keyboards import group_join_kb
from utils import esc, fa, get_db, notify
import handlers_session as hs


def group_panel_text(names, locked, s):
    lines = ["🎧 <b>نوبت منه آهنگ بزارم — گروهی!</b>", ""]
    lines.append(f"👥 اعضا ({fa(len(names))}/{fa(GROUP_MAX_MEMBERS)}):")
    for i, nm in enumerate(names):
        lines.append(f"{fa(i + 1)}. {esc(nm)}")
    if locked:
        lines.append("")
        lines.append("🔒 پیوستن بسته شد!")
        lines.append("⏹ سازنده یا ادمین‌ها می‌تونن با /stop تمومش کنن")
    lines.append("")
    lines.append(f"🎼 هر کس {fa(s['per_user'])} آهنگ همین‌جا بفرسته 🎶")
    if s["state"] == "uploading":
        lines.append("⏳ منتظر آهنگ‌ها...")
    return "\n".join(lines)


async def cmd_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        return
    u = update.effective_user
    db = get_db(context)
    db.upsert_user(u.id, u.username or "", u.full_name or "")
    active = db.get_group_session(chat.id)
    if active:
        if active["state"] == "playing":
            await update.message.reply_text("🎧 یه پلی‌لیست همین‌جا در حال پخشه! با دکمه‌هاش جلو ببرید 🎶")
        else:
            await update.message.reply_text("🎧 یه جلسه فعال همین‌جا دارید! عضو شید و آهنگ بفرستید 🎶")
        return
    sid = db.create_session(
        "group", GROUP_MAX_MEMBERS * GROUP_TRACKS_PER_USER,
        GROUP_TRACKS_PER_USER, u.id, chat.id,
    )
    kb = group_join_kb(sid, locked=False, is_creator=True)
    await update.message.reply_html(
        "🎧 <b>نوبت منه آهنگ بزارم — نسخه گروهی!</b>\n\n"
        "🎶 همه با هم، با یه گوشی، آهنگ‌های همدیگه رو گوش می‌دید!\n"
        f"✋ تا <b>{fa(GROUP_MAX_MEMBERS)} نفر</b> با دکمه پایین میان تو،\n"
        f"🎼 هر کس <b>{fa(GROUP_TRACKS_PER_USER)} آهنگ</b> همین‌جا می‌فرسته،\n"
        "🎵 و پلی‌لیست <b>یکی‌درمیون</b> همین‌جا پخش می‌شه!\n\n"
        "👇 اولین نفری باش:",
        reply_markup=kb,
    )


async def on_group_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = get_db(context)
    uid = q.from_user.id
    _, action, sid_raw = q.data.split(":")
    sid = int(sid_raw)
    s = db.get_session(sid)
    if not s or s["kind"] != "group":
        await q.answer("این جلسه دیگه وجود نداره 🤷", show_alert=True)
        return

    if action == "join":
        if s["state"] != "uploading" or s["locked"]:
            await q.answer("پیوستن بسته شده! 🔒", show_alert=True)
            return
        if db.is_member(sid, uid):
            await q.answer("تو که عضوی! 🎶 آهنگ‌هات رو همین‌جا بفرست.", show_alert=True)
            return
        members = db.get_members(sid)
        if len(members) >= GROUP_MAX_MEMBERS:
            await q.answer("ظرفیت پره! 😬", show_alert=True)
            return
        db.upsert_user(uid, q.from_user.username or "", q.from_user.full_name or "")
        db.add_member(sid, uid)
        members = db.get_members(sid)
        locked = len(members) >= GROUP_MAX_MEMBERS
        if locked:
            db.set_session_fields(sid, locked=1)
        names = [r["name"] or "کاربر" for r in db.member_names(sid)]
        kb = group_join_kb(sid, locked, s["creator_id"] == uid)
        try:
            await q.edit_message_text(
                group_panel_text(names, locked, s),
                parse_mode=ParseMode.HTML, reply_markup=kb,
            )
        except Exception:
            pass
        await q.answer("✋ تو هم اضافه شدی! حالا ۲ آهنگ همین‌جا بفرست 🎶")
        return

    if action == "lock":
        if s["creator_id"] != uid:
            await q.answer("فقط سازنده می‌تونه قفل کنه! 🔒", show_alert=True)
            return
        members = db.get_members(sid)
        if len(members) < 2:
            await q.answer("حداقل ۲ نفر لازمه! 🙏", show_alert=True)
            return
        await q.answer("🔒 بسته شد!")
        db.set_session_fields(sid, locked=1)
        names = [r["name"] or "کاربر" for r in db.member_names(sid)]
        try:
            await q.edit_message_text(
                group_panel_text(names, True, s),
                parse_mode=ParseMode.HTML,
                reply_markup=group_join_kb(sid, True, True),
            )
        except Exception:
            pass
        await hs.maybe_finalize(context, db, sid)
        return

    if action == "cancel":
        if s["creator_id"] != uid:
            await q.answer("فقط سازنده می‌تونه لغو کنه! 🙅", show_alert=True)
            return
        await q.answer("لغو شد ❌")
        db.delete_session(sid)
        try:
            await q.edit_message_text(
                "❌ <b>جلسه گروهی لغو شد.</b>\nبرای شروع دوباره /music بزنید!",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
        return

    await q.answer()


async def on_group_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.message
    u = update.effective_user
    if chat.type not in ("group", "supergroup"):
        return
    db = get_db(context)
    s = db.get_group_session(chat.id)
    if not s or s["state"] != "uploading":
        return
    sid = s["session_id"]
    if not db.is_member(sid, u.id):
        return  # 🤫 آهنگِ کسی که عضو جلسه نیست
    done = db.get_upload(sid, u.id)
    per = s["per_user"]
    if done >= per:
        await msg.reply_html(f"{esc(u.first_name)} سهمیه‌ات پره! 🙌 ({fa(done)}/{fa(per)})")
        return
    file_id, title, performer, dur = hs.track_info(msg)
    db.add_session_track(sid, u.id, file_id, title, performer, dur)
    db.inc_upload(sid, u.id)
    done += 1
    await msg.reply_html(
        f"✅ آهنگ <b>{esc(title)}</b> برای {esc(u.first_name)} ثبت شد! "
        f"({fa(done)}/{fa(per)}) 🎶"
    )
    if not s["locked"]:
        await msg.reply_text("⏳ وقتی همه بیان تو، سازنده «▶️ قفل و ادامه» رو بزنه!")
    await hs.maybe_finalize(context, db, sid)


async def cmd_group_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        return
    uid = update.effective_user.id
    db = get_db(context)
    s = db.get_group_session(chat.id)
    if not s:
        await update.message.reply_text("🤷 جلسه فعالی اینجا نیست.")
        return
    allowed = uid == s["creator_id"]
    if not allowed:
        try:
            m = await context.bot.get_chat_member(chat.id, uid)
            allowed = m.status in ("administrator", "creator")
        except Exception:
            allowed = False
    if not allowed:
        await update.message.reply_text("🙅 فقط سازنده یا ادمین‌های گروه می‌تونن جلسه رو ببندن!")
        return
    db.delete_session(s["session_id"])
    await update.message.reply_text("⏹ جلسه گروهی بسته شد. برای شروع دوباره /music بزنید! 🎧")