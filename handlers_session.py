# -*- coding: utf-8 -*-
"""🎵 پلی‌لیست‌های مچ‌شده اکسپلور، پخش‌کننده یکی‌درمیون، 💚 افراد لایک‌شده، 🔥 محبوب‌ها و پلی‌لیست شخصی"""

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes

from config import PLAYLIST_MODES
from keyboards import (back_main, buddy_list_kb, buddy_panel_kb,
                       buddy_playlist_kb, main_menu, new_playlist_req_kb,
                       personal_del_kb, personal_kb, player_kb,
                       popular_detail_kb, popular_list_kb)
from utils import BANNED_TEXT, edit_or_send, esc, fa, get_db, notify


def track_info(msg):
    """🎼 استخراج مشخصات آهنگ از پیام"""
    a = msg.audio
    if a:
        title = a.title or a.file_name or "بی‌نام"
        return a.file_id, title, (a.performer or ""), (a.duration or 0)
    d = msg.document
    name = d.file_name or "بی‌نام"
    return d.file_id, name, "", 0


def _chats_for(db, s):
    if s["kind"] == "group":
        return [s["chat_id"]]
    return db.get_members(s["session_id"])


def _title_with_genre(n, genre):
    """🏷 عنوان اندازه + سبک، مثل: پلی‌لیست ۶تایی در سبک راک 🎸"""
    if genre:
        return f"پلی‌لیست {fa(n)}تایی در سبک {genre}"
    return f"پلی‌لیست {fa(n)}تایی"


# ---------- ساخت پلی‌لیست مشترک بین دو نفر مچ‌شده (اکسپلور) ----------
async def start_buddy_session(update, context, uid, other, n, genre=""):
    """🎧 ساخت پلی‌لیست مشترک بین دو نفر مچ‌شده — با سبک مشترک اختیاری"""
    db = get_db(context)
    per = PLAYLIST_MODES[n]
    sid = db.create_session("private", n, per, uid, 0)
    db.add_member(sid, uid)
    db.add_member(sid, other)
    me_u = db.get_user(uid)
    ot_u = db.get_user(other)
    my_name = (me_u["display_name"] if me_u and me_u["display_name"] else "دوستت")
    ot_name = (ot_u["display_name"] if ot_u and ot_u["display_name"] else "دوستت")
    size_title = _title_with_genre(n, genre)
    # 🌍 عمومی کردن پلی‌لیست برای نمایش در بخش محبوب‌ها — عنوان شامل سبک است
    db.set_session_fields(
        sid, public=1, genre=genre,
        title=f"{my_name} × {ot_name} — {size_title}",
    )
    genre_line = f"🎼 سبک مشترک پلی‌لیست‌تون: <b>{esc(genre)}</b>\n" if genre else ""
    await notify(
        context, uid,
        f"🎧 <b>{esc(size_title)} مشترک با {esc(ot_name)} ساخته شد!</b>\n\n"
        f"{genre_line}"
        f"🎼 سهمیه تو: <b>{fa(per)} آهنگ</b>\n"
        f"▶️ همین‌جا آهنگ‌هات رو یکی‌یکی بفرست (mp3) 🎶\n\n"
        f"🔥 بعد از آماده شدن، پلی‌لیستتون توی بخش <b>پلی‌لیست‌های محبوب</b> هم به نمایش درمیاد!",
    )
    await notify(
        context, other,
        f"🎧 <b>{esc(my_name)} یه {esc(size_title)} با تو ساخت!</b>\n\n"
        f"{genre_line}"
        f"🎼 سهمیه تو: <b>{fa(per)} آهنگ</b>\n"
        f"▶️ همین‌جا آهنگ‌هات رو یکی‌یکی بفرست (mp3) 🎶\n\n"
        f"🔥 بعد از آماده شدن، پلی‌لیستتون توی بخش <b>پلی‌لیست‌های محبوب</b> هم به نمایش درمیاد!",
    )


# ---------- 💚 افراد لایک‌شده ----------
async def _buddy_list_view(update, context):
    db = get_db(context)
    uid = update.callback_query.from_user.id
    rows = db.list_buddies(uid)
    if not rows:
        await edit_or_send(
            update, context,
            "💚 <b>افراد لایک‌شده</b>\n\n"
            "هنوز با کسی مچ نشدی! 🌱\n"
            "برو اکسپلور 🧭، به هم‌سلیقه‌هات لایک بده و بعد از مچ، "
            "اینجا لیست دوستات و پلی‌لیست‌های مشترکتون رو ببین!",
            back_main(),
        )
        return
    items = []
    for r in rows:
        name = (r["display_name"] or r["tg_name"] or str(r["other_id"]))
        items.append((r["other_id"], name))
    text = (
        "💚 <b>افراد لایک‌شده</b>\n\n"
        f"دوست‌های مچ‌شده‌ات: <b>{fa(len(items))}</b> نفر\n"
        "👇 روی هر نفر بزن تا پلی‌لیست‌های مشترکتون رو ببینی یا پلی‌لیست جدید بخوای:"
    )
    await edit_or_send(update, context, text, buddy_list_kb(items))


async def _buddy_panel_view(update, context, other_id):
    db = get_db(context)
    uid = update.callback_query.from_user.id
    b = db.get_buddy_between(uid, other_id)
    if not b:
        await edit_or_send(
            update, context,
            "🤷 این دوستی دیگه در دسترس نیست.",
            back_main(),
        )
        return
    ou = db.get_user(other_id)
    oname = (ou["display_name"] if ou and ou["display_name"] else "دوستت")
    sess = db.buddy_sessions(uid, other_id)
    items = []
    for s in sess:
        title = s["title"] or "پلی‌لیست مشترک"
        items.append((s["session_id"], title))
    if items:
        text = (
            f"👤 <b>{esc(oname)}</b> 💚\n\n"
            f"🎧 پلی‌لیست‌های مشترک شما: <b>{fa(len(items))}</b>\n"
            "🔹 برای گوش دادن به پلی‌لیست‌های قبلی، رویشون بزن.\n"
            "🔹 برای پلی‌لیست جدید، اندازه‌اش رو انتخاب کن — درخواست برای طرف مقابل ارسال می‌شه:"
        )
    else:
        text = (
            f"👤 <b>{esc(oname)}</b> 💚\n\n"
            "هنوز پلی‌لیست مشترکی ندارید! 🌱\n"
            "👇 یه اندازه انتخاب کن — درخواست برای طرف مقابل ارسال می‌شه:"
        )
    await edit_or_send(update, context, text, buddy_panel_kb(other_id, items))


async def _buddy_playlist_view(update, context, sid):
    db = get_db(context)
    uid = update.callback_query.from_user.id
    s = db.get_session(sid)
    if not s or not db.is_member(sid, uid):
        await edit_or_send(
            update, context,
            "🤷 این پلی‌لیست در دسترس نیست.",
            back_main(),
        )
        return
    members = db.get_members(sid)
    other = next((m for m in members if m != uid), uid)
    names = [r["name"] or "کاربر" for r in db.member_names(sid)]
    tracks = db.session_tracks(sid)
    title = s["title"] or (" × ".join(names) if names else "پلی‌لیست مشترک")
    genre_line = f"🎼 سبک پلی‌لیست: <b>{esc(s['genre'])}</b>\n" if s["genre"] else ""
    text = (
        f"🎧 <b>{esc(title)}</b>\n\n"
        f"{genre_line}"
        f"👥 سازندگان: {esc('، '.join(names)) if names else '—'}\n"
        f"🎵 تعداد آهنگ‌ها: <b>{fa(len(tracks))}</b>\n\n"
        "👇 برای گوش دادن، دکمه پایین رو بزن:"
    )
    await edit_or_send(update, context, text, buddy_playlist_kb(sid, other))


async def _buddy_playlist_play(context, db, uid, sid):
    """🎧 پخش آهنگ‌های یک پلی‌لیست مشترک برای خود کاربر"""
    s = db.get_session(sid)
    if not s or not db.is_member(sid, uid):
        await notify(context, uid, "🤷 این پلی‌لیست در دسترس نیست.")
        return
    tracks = db.session_tracks(sid)
    if not tracks:
        await notify(context, uid, "این پلی‌لیست هنوز آهنگی نداره! ⏳")
        return
    title = s["title"] or "پلی‌لیست مشترک"
    names = {r["user_id"]: (r["name"] or "کاربر") for r in db.member_names(sid)}
    total = min(len(tracks), 20)
    await notify(
        context, uid,
        f"🎧 <b>{esc(title)}</b>\n🎵 پخش {fa(total)} آهنگ شروع شد! 🎧",
    )
    for i, t in enumerate(tracks[:20]):
        performer = esc(t["performer"]) if t["performer"] else "هنرمند نامشخص"
        caption = (
            f"💚 <b>{esc(title)}</b>\n"
            f"🎵 <b>{esc(t['title'])}</b>\n"
            f"🎤 {performer}\n"
            f"🎯 آهنگ {fa(i + 1)} از {fa(total)}\n"
            f"📦 اضافه‌شده توسط: {esc(names.get(t['user_id'], 'کاربر'))}"
        )
        try:
            await context.bot.send_audio(
                uid, audio=t["file_id"], caption=caption,
                parse_mode=ParseMode.HTML,
                title=t["title"] or None, performer=t["performer"] or None,
            )
        except (Forbidden, BadRequest):
            break
    await notify(
        context, uid,
        "🎉 تموم شد! برای پلی‌لیست جدید، از پنل دوستت اندازه رو انتخاب کن 💚",
    )


async def on_blist_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = get_db(context)
    uid = q.from_user.id
    parts = q.data.split(":")
    route = parts[0]

    if route == "blist":
        await q.answer("💚")
        await _buddy_list_view(update, context)
        return

    # از اینجا به بعد bl:...
    try:
        arg = int(parts[2]) if len(parts) > 2 else 0
    except ValueError:
        await q.answer("دستور نامعتبره 🤔", show_alert=True)
        return

    if parts[1] == "user":
        await q.answer("👤")
        await _buddy_panel_view(update, context, arg)
        return

    if parts[1] == "back":
        await q.answer("🔙")
        await _buddy_panel_view(update, context, arg)
        return

    if parts[1] == "open":
        await q.answer("🎧")
        await _buddy_playlist_view(update, context, arg)
        return

    if parts[1] == "play":
        if db.is_banned(uid):
            await q.answer(BANNED_TEXT, show_alert=True)
            return
        await q.answer("🎧 پخش شروع شد!")
        await _buddy_playlist_play(context, db, uid, arg)
        return

    if parts[1] == "blsize":
        # 🆕 درخواست ساخت پلی‌لیست جدید — نوتیف برای طرف مقابل
        n = arg
        try:
            other_id = int(parts[3]) if len(parts) > 3 else 0
        except ValueError:
            other_id = 0
        if n not in PLAYLIST_MODES or not other_id:
            await q.answer("دستور نامعتبره 🤔", show_alert=True)
            return
        if not db.get_buddy_between(uid, other_id):
            await q.answer("این دوستی معتبر نیست 🤷", show_alert=True)
            return
        await q.answer("📨 نوتیف ارسال شد!")
        my_u = db.get_user(uid)
        my_name = (my_u["display_name"] if my_u and my_u["display_name"]
                   else (q.from_user.first_name or "دوستت"))
        per = PLAYLIST_MODES[n]
        # ✉️ پیام به درخواست‌دهنده
        await notify(
            context, uid,
            f"📨 <b>نوتیف برای طرف مقابل ارسال شد!</b>\n\n"
            f"🎧 درخواست ساخت <b>پلی‌لیست {fa(n)}تایی</b> (هر نفر {fa(per)} آهنگ) "
            f"برای <b>{esc(my_name)}</b> رفت.\n"
            f"⏳ به‌محض قبول کردنش، پلی‌لیست ساخته می‌شه و بهت خبر می‌دیم!",
        )
        # 🔔 پیام به طرف مقابل با دکمه قبول/رد
        await notify(
            context, other_id,
            f"🎧 <b>{esc(my_name)}</b> می‌خواد باهات یه "
            f"<b>پلی‌لیست {fa(n)}تایی</b> (هر نفر {fa(per)} آهنگ) جدید بسازه!\n\n"
            f"👇 موافقی؟",
            new_playlist_req_kb(n, uid),
        )
        return

    if parts[1] == "ynew":
        # ✅ قبول درخواست ساخت پلی‌لیست جدید
        n = arg
        try:
            req_id = int(parts[3]) if len(parts) > 3 else 0
        except ValueError:
            req_id = 0
        if n not in PLAYLIST_MODES or not req_id:
            await q.answer("دستور نامعتبره 🤔", show_alert=True)
            return
        if uid == req_id:
            await q.answer("این دکمه برای تو نیست 🙅", show_alert=True)
            return
        if not db.get_buddy_between(uid, req_id):
            await q.answer("این دوستی معتبر نیست 🤷", show_alert=True)
            return
        # 🧹 بستن جلسات نیمه‌کاره قدیمی
        db.close_user_private_sessions(uid)
        db.close_user_private_sessions(req_id)
        await q.answer("🎧 پلی‌لیست ساخته شد!")
        try:
            if q.message and q.message.text:
                await q.edit_message_text(
                    "✅ قبول کردی! 🎧 پلی‌لیست مشترک ساخته شد — جفت‌تون آهنگ‌هاتون رو بفرستید!",
                    parse_mode=ParseMode.HTML,
                )
            elif q.message:
                await q.edit_message_caption(
                    caption="✅ قبول کردی! 🎧 پلی‌لیست مشترک ساخته شد — جفت‌تون آهنگ‌هاتون رو بفرستید!",
                    parse_mode=ParseMode.HTML,
                )
        except Exception:
            pass
        await start_buddy_session(update, context, uid, req_id, n, genre="")
        return

    if parts[1] == "nnew":
        # ❌ رد درخواست ساخت پلی‌لیست جدید
        try:
            req_id = int(parts[3]) if len(parts) > 3 else 0
        except ValueError:
            req_id = 0
        await q.answer("❌ رد شد")
        try:
            if q.message and q.message.text:
                await q.edit_message_text("❌ درخواست رد شد.", parse_mode=ParseMode.HTML)
            elif q.message:
                await q.edit_message_caption(caption="❌ درخواست رد شد.", parse_mode=ParseMode.HTML)
        except Exception:
            pass
        if req_id:
            await notify(
                context, req_id,
                "🕊 <b>درخواستت رد شد!</b>\n"
                "طرف مقابل فعلاً برای ساخت پلی‌لیست جدید آماده نیست؛ بعداً دوباره امتحان کن!",
            )
        return

    await q.answer()


# ---------- دریافت آهنگ در پیوی ----------
async def on_private_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    u = update.effective_user
    msg = update.message
    db.upsert_user(u.id, u.username or "", u.full_name or "")
    if db.is_banned(u.id):
        await msg.reply_html(BANNED_TEXT)
        return

    if context.user_data.get("personal_add"):
        file_id, title, performer, dur = track_info(msg)
        db.add_personal_track(u.id, file_id, title, performer, dur)
        cnt = len(db.personal_tracks(u.id))
        await msg.reply_html(
            f"✅ به <b>پلی‌لیست شخصی</b> اضافه شد! 🎵 ({fa(cnt)} آهنگ)\n"
            f"➕ ادامه بده یا /done بزن."
        )
        return

    s = db.get_user_upload_session(u.id, "private")
    if not s:
        await msg.reply_html(
            "🎧 برای فرستادن آهنگ، اول از <b>اکسپلور 🧭</b> مچ شو و پلی‌لیست مشترک بساز، "
            "یا <b>پلی‌لیست من</b> رو انتخاب کن!"
        )
        return
    sid = s["session_id"]
    # 🧹 جلسه خصوصیِ تک‌نفره یعنی نیمه‌کاره قدیمی است؛ خودکار بسته می‌شود
    if len(db.get_members(sid)) < 2:
        db.set_session_fields(sid, state="done")
        await msg.reply_html(
            "🧹 یه پلی‌لیست قدیمیِ نیمه‌کاره بسته شد!\n\n"
            "🎧 برای فرستادن آهنگ، از <b>اکسپلور 🧭</b> مچ شو و پلی‌لیست مشترک بساز، "
            "یا <b>پلی‌لیست من</b> رو انتخاب کن."
        )
        return
    per = s["per_user"]
    done = db.get_upload(sid, u.id)
    if done >= per:
        await msg.reply_text("🙌 سهمیه‌ات پره! منتظر طرف مقابل بمون تا پلی‌لیست شروع شه.")
        return
    file_id, title, performer, dur = track_info(msg)
    db.add_session_track(sid, u.id, file_id, title, performer, dur)
    db.inc_upload(sid, u.id)
    done += 1
    if done < per:
        await msg.reply_html(
            f"✅ ثبت شد! 🎵 ({fa(done)}/{fa(per)})\n▶️ آهنگ بعدی رو بفرست..."
        )
    else:
        await msg.reply_html(
            f"✅ آخری‌اش هم ثبت شد! 🎉 ({fa(done)}/{fa(per)})\n"
            f"⏳ تا سهمیه طرف مقابل پر شه صبر کن..."
        )
    await maybe_finalize(context, db, sid)


# ---------- شروع پخش ----------
async def maybe_finalize(context, db, sid):
    s = db.get_session(sid)
    if not s or s["state"] != "uploading":
        return
    members = db.get_members(sid)
    need = 2 if s["kind"] == "private" else 1
    if len(members) < need:
        return
    if s["kind"] == "group" and not s["locked"]:
        return
    for m in members:
        if db.get_upload(sid, m) < s["per_user"]:
            return
    # 🎚 چیدن یکی‌درمیون آهنگ‌های اعضا
    slot = 0
    for i in range(s["per_user"]):
        for m in members:
            t = db.member_track_at(sid, m, i)
            if t:
                db.set_track_slot(t["id"], slot)
                slot += 1
    db.set_session_fields(sid, state="playing", current_index=0)
    s = db.get_session(sid)
    chats = _chats_for(db, s)
    for c in chats:
        await notify(
            context, c,
            "🎉 <b>پلی‌لیست آماده شد!</b>\n"
            "🎶 آهنگ‌ها یکی‌درمیون پخش می‌شن — با دکمه‌ها جلو ببر!\n"
            "🔥 پلی‌لیستتون الان توی بخش «محبوب‌ها» هم قابل لایک و گوش دادنه!",
        )
    await send_current(context, db, s, chats)


async def send_current(context, db, s, chats=None):
    sid = s["session_id"]
    tracks = db.session_tracks(sid)
    if not tracks:
        return
    idx = max(0, min(s["current_index"], len(tracks) - 1))
    t = tracks[idx]
    names = {r["user_id"]: (r["name"] or "کاربر") for r in db.member_names(sid)}
    performer = esc(t["performer"]) if t["performer"] else "هنرمند نامشخص"
    caption = (
        f"🎵 <b>{esc(t['title'])}</b>\n"
        f"🎤 {performer}\n"
        f"🎯 آهنگ {fa(idx + 1)} از {fa(len(tracks))}\n"
        f"📦 اضافه‌شده توسط: {esc(names.get(t['user_id'], 'کاربر'))}"
    )
    kb = player_kb(sid)
    chats = chats if chats is not None else _chats_for(db, s)
    for c in chats:
        try:
            await context.bot.send_audio(
                c, audio=t["file_id"], caption=caption,
                parse_mode=ParseMode.HTML, reply_markup=kb,
                title=t["title"] or None, performer=t["performer"] or None,
            )
        except (Forbidden, BadRequest):
            pass


# ---------- پخش‌کننده ----------
async def on_player_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = get_db(context)
    uid = q.from_user.id
    _, action, sid_raw = q.data.split(":")
    sid = int(sid_raw)
    s = db.get_session(sid)
    if not s or not db.is_member(sid, uid):
        await q.answer("این پلی‌لیست مال تو نیست 🙅", show_alert=True)
        return
    if s["state"] != "playing":
        await q.answer("این پلی‌لیست الان در حال پخش نیست ⏸", show_alert=True)
        return
    tracks = db.session_tracks(sid)
    n = len(tracks)
    idx = s["current_index"]

    if action == "list":
        await q.answer()
        lines = []
        for i, t in enumerate(tracks):
            mark = "▶️" if i == idx else f"{fa(i + 1)}."
            lines.append(f"{mark} {esc(t['title'])}")
        await notify(context, uid, "📋 <b>لیست پخش:</b>\n\n" + "\n".join(lines))
        return

    if action == "stop":
        await q.answer("متوقف شد ⏹")
        db.set_session_fields(sid, state="done")
        for c in _chats_for(db, s):
            await notify(context, c, "⏹ <b>پخش متوقف شد.</b>")
        return

    if action == "next":
        idx += 1
    elif action == "prev":
        idx = max(0, idx - 1)
    elif action == "restart":
        idx = 0

    if idx >= n:
        await q.answer("تموم شد 🎉")
        db.set_session_fields(sid, state="done")
        for c in _chats_for(db, s):
            await notify(
                context, c,
                "🎉 <b>پلی‌لیست تموم شد!</b>\nامیدوارم خوش گذشته باشه!\n"
                "🔥 یادت باشه پلی‌لیستتون توی بخش «محبوب‌ها» منتظر لایک‌هاست! ❤️",
            )
        return

    await q.answer(f"🎵 آهنگ {fa(idx + 1)} از {fa(n)}")
    db.set_session_fields(sid, current_index=idx)
    s = db.get_session(sid)
    await send_current(context, db, s, _chats_for(db, s))


# ---------- 🔥 پلی‌لیست‌های محبوب ----------
async def popular_panel(update, context):
    """🔥 نمایش پلی‌لیست‌های محبوب مرتب بر اساس لایک"""
    db = get_db(context)
    items = db.popular_playlists()
    if not items:
        await edit_or_send(
            update, context,
            "🔥 <b>پلی‌لیست‌های محبوب</b>\n\n"
            "هنوز هیچ پلی‌لیستی ثبت نشده! 🌱\n"
            "اولین نفر باش: برو اکسپلور 🧭، مچ شو 💚 و پلی‌لیست مشترک بسازید!",
            back_main(),
        )
        return
    lines = []
    kb_items = []
    for i, s in enumerate(items):
        title = s["title"] or "بدون عنوان"
        lines.append(
            f"{fa(i + 1)}. ❤️ <b>{fa(s['likes'])}</b> | {esc(title)} "
            f"({fa(s['ntracks'])} آهنگ)"
        )
        kb_items.append((s["session_id"], title, s["likes"]))
    text = (
        "🔥 <b>پلی‌لیست‌های محبوب</b>\n\n"
        "پلی‌لیست‌هایی که توی اکسپلور ساخته شدن، به ترتیب لایک:\n\n"
        + "\n".join(lines)
        + "\n\n👇 روی هر کدوم بزن تا لایکش کنی و گوش بدی!"
    )
    await edit_or_send(update, context, text, popular_list_kb(kb_items))


async def _show_popular_detail(update, context, sid):
    db = get_db(context)
    uid = update.callback_query.from_user.id
    s = db.get_session(sid)
    if not s or not s["public"]:
        await edit_or_send(
            update, context,
            "🤷 این پلی‌لیست دیگه در دسترس نیست.",
            back_main(),
        )
        return
    names = [r["name"] or "کاربر" for r in db.member_names(sid)]
    title = s["title"] or (" × ".join(names) if names else "پلی‌لیست")
    likes = db.like_count(sid)
    tracks = db.session_tracks(sid)
    liked = db.has_liked(sid, uid)
    genre_line = f"🎼 سبک پلی‌لیست: <b>{esc(s['genre'])}</b>\n" if s["genre"] else ""
    text = (
        f"🎧 <b>{esc(title)}</b>\n\n"
        f"{genre_line}"
        f"👥 سازندگان: {esc('، '.join(names)) if names else '—'}\n"
        f"🎵 تعداد آهنگ‌ها: {fa(len(tracks))}\n"
        f"❤️ لایک‌ها: <b>{fa(likes)}</b>\n\n"
        "اگه سلیقه‌ت رو می‌کشه، لایکش کن و آهنگ‌هاش رو گوش بده! ❤️"
    )
    await edit_or_send(update, context, text, popular_detail_kb(sid, liked))


async def on_popular_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = get_db(context)
    uid = q.from_user.id
    parts = q.data.split(":")
    action = parts[1]

    if action == "refresh":
        await q.answer("🔄")
        await popular_panel(update, context)
        return

    try:
        sid = int(parts[2])
    except (IndexError, ValueError):
        await q.answer("دستور نامعتبره 🤔", show_alert=True)
        return

    s = db.get_session(sid)
    if not s or not s["public"]:
        await q.answer("این پلی‌لیست دیگه در دسترس نیست 🤷", show_alert=True)
        return

    if action == "open":
        await q.answer()
        await _show_popular_detail(update, context, sid)
        return

    if action == "like":
        if db.has_liked(sid, uid):
            db.unlike_playlist(sid, uid)
            await q.answer("💔 لایکت برداشته شد")
        else:
            db.like_playlist(sid, uid)
            await q.answer("❤️ لایک شد!")
        await _show_popular_detail(update, context, sid)
        return

    if action == "play":
        tracks = db.session_tracks(sid)
        if not tracks:
            await q.answer("این پلی‌لیست هنوز آهنگی نداره! ⏳", show_alert=True)
            return
        await q.answer("🎧 پخش شروع شد!")
        title = s["title"] or "پلی‌لیست محبوب"
        names = {r["user_id"]: (r["name"] or "کاربر") for r in db.member_names(sid)}
        total = min(len(tracks), 20)
        await notify(
            context, uid,
            f"🎧 <b>{esc(title)}</b>\n🎵 پخش {fa(total)} آهنگ شروع شد! 🎧",
        )
        for i, t in enumerate(tracks[:20]):
            performer = esc(t["performer"]) if t["performer"] else "هنرمند نامشخص"
            caption = (
                f"🔥 <b>{esc(title)}</b>\n"
                f"🎵 <b>{esc(t['title'])}</b>\n"
                f"🎤 {performer}\n"
                f"🎯 آهنگ {fa(i + 1)} از {fa(total)}\n"
                f"📦 اضافه‌شده توسط: {esc(names.get(t['user_id'], 'کاربر'))}"
            )
            try:
                await context.bot.send_audio(
                    uid, audio=t["file_id"], caption=caption,
                    parse_mode=ParseMode.HTML,
                    title=t["title"] or None, performer=t["performer"] or None,
                )
            except (Forbidden, BadRequest):
                break
        await notify(
            context, uid,
            "🎉 تموم شد! اگه خوشت اومد، توی جزئیات پلی‌لیست بهش لایک بده ❤️",
            popular_detail_kb(sid, db.has_liked(sid, uid)),
        )
        return

    await q.answer()


# ---------- پلی‌لیست شخصی ----------
async def personal_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    uid = update.callback_query.from_user.id
    tracks = db.personal_tracks(uid)
    lines = []
    for i, t in enumerate(tracks[:10]):
        lines.append(f"{fa(i + 1)}. {esc(t['title'])}")
    more = f"\n... و {fa(len(tracks) - 10)} آهنگ دیگه" if len(tracks) > 10 else ""
    body = ("\n".join(lines) + more) if lines else "هنوز آهنگی نداری! با «➕ افزودن آهنگ» شروع کن 🎶"
    text = f"🎧 <b>پلی‌لیست شخصی من</b>\n\n🎵 تعداد آهنگ‌ها: <b>{fa(len(tracks))}</b>\n\n{body}"
    await edit_or_send(update, context, text, personal_kb())


async def on_personal_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = get_db(context)
    uid = q.from_user.id
    data = q.data

    if data == "per:add":
        await q.answer("حالت افزودن روشن شد 🎶")
        context.user_data["personal_add"] = True
        await notify(
            context, uid,
            "➕ <b>حالت افزودن آهنگ روشن شد!</b>\n"
            "🎶 حالا آهنگ‌هات رو بفرست (mp3).\n"
            "✅ هر وقت خواستی /done بزن.",
        )
        return

    if data == "per:play":
        tracks = db.personal_tracks(uid)
        if not tracks:
            await q.answer("هنوز آهنگی نداری! 🎵 اول اضافه کن", show_alert=True)
            return
        await q.answer("پخش شروع شد 🎧")
        total = min(len(tracks), 20)
        for i, t in enumerate(tracks[:20]):
            try:
                await context.bot.send_audio(
                    uid, audio=t["file_id"],
                    caption=(f"🎧 پلی‌لیست شخصی — {fa(i + 1)}/{fa(total)}\n"
                             f"🎵 {esc(t['title'])}"),
                    parse_mode=ParseMode.HTML,
                    title=t["title"] or None, performer=t["performer"] or None,
                )
            except (Forbidden, BadRequest):
                break
        return

    if data == "per:del":
        tracks = db.personal_tracks(uid)
        if not tracks:
            await q.answer("لیست خالیه! 🤷", show_alert=True)
            return
        await q.answer()
        await edit_or_send(update, context, "🗑 کدوم آهنگ حذف شه؟", personal_del_kb(tracks))
        return

    if data.startswith("per:delone:"):
        try:
            tid = int(data.split(":")[2])
        except (IndexError, ValueError):
            await q.answer()
            return
        db.delete_personal_track(tid, uid)
        await q.answer("حذف شد ✅")
        tracks = db.personal_tracks(uid)
        if not tracks:
            await personal_panel(update, context)
        else:
            await edit_or_send(update, context, "🗑 کدوم آهنگ حذف شه؟", personal_del_kb(tracks))
        return

    if data == "per:back":
        await q.answer()
        await personal_panel(update, context)
        return

    await q.answer()