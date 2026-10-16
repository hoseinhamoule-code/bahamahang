# -*- coding: utf-8 -*-
"""🧭 اکسپلور — اول نفرات جدید، بعد دیده‌شده‌ها، سهمیه + کانال اجباری + انتخاب سبک مشترک"""

import json

from telegram import CallbackQuery
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import (EXPLORE_CHANNEL_BATCH, EXPLORE_FREE_VIEWS, GENRES,
                    PLAYLIST_MODES)
from keyboards import (back_main, buddy_chat_kb, buddy_kb, channel_join_kb,
                       explore_kb, genre_pick_kb, like_card_kb)
from utils import (edit_or_send, esc, fa, force_channel, get_db,
                   is_channel_member, match_score, notify)
import handlers_session as hs


def _size_lines():
    """🎼 متن نمایش تعداد آهنگ‌های هر اندازه پلی‌لیست"""
    return "\n".join(
        f"▫️ {fa(n)}تایی — هر نفر {fa(p)} آهنگ"
        for n, p in sorted(PLAYLIST_MODES.items())
    )


def _profile_lines(u):
    genres = ", ".join(json.loads(u["genres"] or "[]")) or "—"
    singers = ", ".join(json.loads(u["singers"] or "[]")) or "—"
    return (
        f"🏙 شهر: {esc(u['city']) or '—'}\n"
        f"🎂 سن: {fa(u['age'])}\n"
        f"🎼 سبک‌های محبوب: {esc(genres)}\n"
        f"🎤 خواننده‌های محبوب: {esc(singers)}"
    )


def _card_text(u, score):
    return (
        "🧭 <b>اکسپلور سلیقه‌ها</b>\n\n"
        f"👤 اسم: <b>{esc(u['display_name'])}</b>\n"
        f"{_profile_lines(u)}\n\n"
        f"💚 میزان سلیقه مشترک: <b>{fa(score)}٪</b>"
    )


def _like_card_text(u, score):
    """💚 متن کارت لایک — پروفایل کامل کسی که لایک کرده"""
    return (
        "💚 <b>یه لایک جدید داری!</b>\n\n"
        f"👤 <b>{esc(u['display_name'])}</b> بهت لایک داده! 🥳\n"
        f"{_profile_lines(u)}\n\n"
        f"💚 سلیقه مشترک شما: <b>{fa(score)}٪</b>\n\n"
        "👇 اگه تو هم بهش لایک بدی، همین الان مچ می‌شید!"
    )


def _display_name(db, uid, fallback="دوستت"):
    u = db.get_user(uid)
    return (u["display_name"] if u and u["display_name"] else fallback)


def _common_genres(db, a_id, b_id):
    """🎼 سبک‌های موسیقی مشترک دو نفر (به ترتیب لیست اصلی GENRES)"""
    ua = db.get_user(a_id)
    ub = db.get_user(b_id)
    if not ua or not ub:
        return []
    ga = set(json.loads(ua["genres"] or "[]"))
    gb = set(json.loads(ub["genres"] or "[]"))
    common = ga & gb
    return [g for g in GENRES if g in common]


def _views_limit(me) -> int:
    return EXPLORE_FREE_VIEWS + int(me["explore_unlocked"] or 0)


async def explore_open(update, context):
    q = update.callback_query
    db = get_db(context)
    uid = q.from_user.id
    me = db.get_user(uid)
    if not db.profile_ready(me):
        await q.answer("اول پروفایلت رو کامل کن! 👤", show_alert=True)
        return
    await q.answer("🧭")
    context.user_data["ex_seen"] = set()
    await show_card(update, context)


async def _show_channel_wall(update, context, db, me):
    """🔒 دیوار عضویت کانال وقتی سهمیه رایگان تمام شده"""
    ch = force_channel(db)
    link = f"https://t.me/{ch.lstrip('@')}" if ch else "https://t.me/telegram"
    used = int(me["explore_views"] or 0)
    text = (
        "🔒 <b>سهمیه رایگان اکسپلور تموم شد!</b>\n\n"
        f"🎯 {fa(EXPLORE_FREE_VIEWS)} نفر اول رایگان بودند و تا حالا "
        f"<b>{fa(used)}</b> نفر دیدی.\n\n"
        f"📣 برای دیدن <b>{fa(EXPLORE_CHANNEL_BATCH)} نفر بعدی</b>، عضو کانال رسمی ما شو "
        "و بعد «✅ عضو شدم» رو بزن:"
    )
    await edit_or_send(update, context, text, channel_join_kb(link))


async def show_card(update, context):
    db = get_db(context)
    uid = update.callback_query.from_user.id
    me = db.get_user(uid)
    if not me:
        return

    # 🔒 بررسی سهمیه دیدن نفرات
    ch = force_channel(db)
    if ch and int(me["explore_views"] or 0) >= _views_limit(me):
        await _show_channel_wall(update, context, db, me)
        return

    seen_ids = context.user_data.setdefault("ex_seen", set())

    def build_pool():
        pool = [(u, False) for u in db.explore_new_users(uid)
                if u["user_id"] not in seen_ids]
        pool += [(u, True) for u in db.explore_seen_users(uid)
                 if u["user_id"] not in seen_ids]
        return pool

    pool = build_pool()
    if not pool and seen_ids:
        # 🔁 همه را در این جلسه دیده؛ کش جلسه را خالی کن تا دوباره بچرخند
        seen_ids.clear()
        pool = build_pool()
    if not pool:
        await edit_or_send(
            update, context,
            "🌙 <b>فعلاً کسی جدیدی نمونده!</b>\n"
            "دوستانت رو دعوت کن به ربات، بعداً برگرد! 😉",
            back_main(),
        )
        return

    u, was_seen = pool[0]
    seen_ids.add(u["user_id"])
    db.inc_explore_views(uid)

    me_g = json.loads(me["genres"] or "[]")
    me_s = json.loads(me["singers"] or "[]")
    u_g = json.loads(u["genres"] or "[]")
    u_s = json.loads(u["singers"] or "[]")
    score = match_score(me_g, me_s, u_g, u_s)
    text = _card_text(u, score)
    if was_seen:
        text += "\n\n👁 <i>قبلا دیده شده</i>"
    kb = explore_kb(u["user_id"])
    if u["photo_file_id"]:
        try:
            await context.bot.send_photo(
                uid, photo=u["photo_file_id"],
                caption=text, parse_mode=ParseMode.HTML, reply_markup=kb,
            )
            return
        except Exception:
            pass
    await edit_or_send(update, context, text, kb)


async def _edit_to_match(q: CallbackQuery, other_name: str):
    """✏️ ویرایش کارت فعلی به پیام «مچ شدید»"""
    text = f"🎉 <b>مچ شدید!</b>\n\nشما و <b>{esc(other_name)}</b> به هم لایک دادید!"
    try:
        if q.message and q.message.text:
            await q.edit_message_text(text, parse_mode=ParseMode.HTML)
        elif q.message:
            await q.edit_message_caption(caption=text, parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def _match_notify(context, db, uid, tid):
    """🎉 پیام‌های مچ برای هر دو نفر — با تشخیص لایک‌کننده اول"""
    bid_obj = db.get_buddy_between(uid, tid)
    bid = bid_obj["id"] if bid_obj else db.create_buddy(uid, tid)
    first = db.get_first_liker(uid, tid)
    second = tid if first == uid else uid
    first_name = _display_name(db, first)
    second_name = _display_name(db, second)
    u_first = db.get_user(first)
    u_second = db.get_user(second)
    both_pro = bool(u_first and u_first["is_pro"] and u_second and u_second["is_pro"])
    sizes = _size_lines()

    if first == uid:
        await notify(
            context, uid,
            f"🎉 <b>مچ شدید!</b>\nشما و <b>{esc(second_name)}</b> به هم لایک دادید! 💚\n\n"
            f"🏅 تو زودتر لایک دادی؛ پس انتخاب‌ها با توئه:\n"
            f"۱️⃣ اول تعداد آهنگ‌های پلی‌لیست مشترک:\n{sizes}\n"
            f"۲️⃣ بعد از بین <b>سبک‌های مشترک‌تون</b> 🎼 یه سبک انتخاب می‌کنی!\n\n"
            f"👇 برای شروع، یه اندازه انتخاب کن:",
            buddy_kb(bid, both_pro),
        )
        await notify(
            context, tid,
            f"🎉 <b>مچ شدید!</b>\nشما و <b>{esc(first_name)}</b> به هم لایک دادید! 💚\n\n"
            f"🎧 {esc(first_name)} زودتر لایک داده و داره تعداد آهنگ‌ها و "
            f"<b>سبک مشترک پلی‌لیست</b> 🎼 رو انتخاب می‌کنه:\n{sizes}\n\n"
            f"⏳ به‌محض انتخاب، پلی‌لیست ساخته می‌شه و بهت خبر می‌دیم!",
            buddy_chat_kb(bid, both_pro),
        )
    else:
        await notify(
            context, uid,
            f"🎉 <b>مچ شدید!</b>\nشما و <b>{esc(second_name)}</b> به هم لایک دادید! 💚\n\n"
            f"🎧 {esc(second_name)} زودتر لایک داده و داره تعداد آهنگ‌ها و "
            f"<b>سبک مشترک پلی‌لیست</b> 🎼 رو انتخاب می‌کنه:\n{sizes}\n\n"
            f"⏳ به‌محض انتخاب، پلی‌لیست ساخته می‌شه و بهت خبر می‌دیم!",
            buddy_chat_kb(bid, both_pro),
        )
        await notify(
            context, tid,
            f"🎉 <b>مچ شدید!</b>\nشما و <b>{esc(first_name)}</b> به هم لایک دادید! 💚\n\n"
            f"🏅 تو زودتر لایک دادی؛ پس انتخاب‌ها با توئه:\n"
            f"۱️⃣ اول تعداد آهنگ‌های پلی‌لیست مشترک:\n{sizes}\n"
            f"۲️⃣ بعد از بین <b>سبک‌های مشترک‌تون</b> 🎼 یه سبک انتخاب می‌کنی!\n\n"
            f"👇 برای شروع، یه اندازه انتخاب کن:",
            buddy_kb(bid, both_pro),
        )


async def _send_like_card(context, db, tid, liker_id):
    """💚 ارسال کارت لایک با پروفایل کامل لایک‌کننده برای گیرنده"""
    me = db.get_user(tid)
    lk = db.get_user(liker_id)
    if not lk or not me:
        return
    my_g = json.loads(me["genres"] or "[]")
    my_s = json.loads(me["singers"] or "[]")
    lk_g = json.loads(lk["genres"] or "[]")
    lk_s = json.loads(lk["singers"] or "[]")
    score = match_score(my_g, my_s, lk_g, lk_s)
    text = _like_card_text(lk, score)
    kb = like_card_kb(liker_id)
    if lk["photo_file_id"]:
        try:
            await context.bot.send_photo(
                tid, photo=lk["photo_file_id"],
                caption=text, parse_mode=ParseMode.HTML, reply_markup=kb,
            )
            return
        except Exception:
            pass
    await notify(context, tid, text, kb)


async def on_explore_cb(update, context):
    q = update.callback_query
    db = get_db(context)
    uid = q.from_user.id
    _, action, tid_raw = q.data.split(":")
    tid = int(tid_raw)
    me = db.get_user(uid)
    if not db.profile_ready(me):
        await q.answer("اول پروفایلت رو کامل کن! 👤", show_alert=True)
        return

    # 🔒 بررسی عضویت کانال (دکمه «عضو شدم»)
    if action == "chan":
        if await is_channel_member(context, db, uid):
            db.unlock_explore_views(uid, EXPLORE_CHANNEL_BATCH)
            await q.answer(f"🎉 {fa(EXPLORE_CHANNEL_BATCH)} نفر بعدی باز شد!")
            await show_card(update, context)
        else:
            await q.answer("❌ هنوز عضو کانال نشدی! اول عضو شو، بعد دکمه رو بزن.",
                           show_alert=True)
        return

    # 💔 رد مستقیم از روی کارت لایک
    if action == "directpass":
        db.add_swipe(uid, tid, "pass")
        await q.answer("💔 رد شد")
        try:
            if q.message and q.message.text:
                await q.edit_message_text(
                    "💔 ردش کردی. بریم دنبال نفر بعدی! 🧭",
                    parse_mode=ParseMode.HTML,
                )
            elif q.message:
                await q.edit_message_caption(
                    caption="💔 ردش کردی. بریم دنبال نفر بعدی! 🧭",
                    parse_mode=ParseMode.HTML,
                )
        except Exception:
            pass
        return

    # 💚 لایک مستقیم از روی کارت لایک
    if action == "directlike":
        if db.get_buddy_between(uid, tid):
            await q.answer("قبلاً مچ شدید! 🎉", show_alert=True)
            return
        other = db.get_swipe(tid, uid)
        db.add_swipe(uid, tid, "like")
        if other and other["action"] == "like":
            await q.answer("🎉 مچ شدید!")
            other_name = _display_name(db, tid)
            await _edit_to_match(q, other_name)
            await _match_notify(context, db, uid, tid)
        else:
            await q.answer("💚 لایک شد! منتظر لایک طرف بمون 🤞")
        return

    if action == "skip":
        await q.answer("⏭")
        await show_card(update, context)
        return

    # 📝 ثبت لایک/رد داخل اکسپلور
    prev = db.get_swipe(uid, tid)
    already_liked = bool(prev and prev["action"] == "like")
    db.add_swipe(uid, tid, "like" if action == "like" else "pass")

    if action == "pass":
        await q.answer("💔 رد شد")
        await show_card(update, context)
        return

    # 💚 لایک عادی داخل اکسپلور
    other = db.get_swipe(tid, uid)
    if other and other["action"] == "like":
        await q.answer("🎉 مچ شدید!")
        other_name = _display_name(db, tid)
        await _edit_to_match(q, other_name)
        await _match_notify(context, db, uid, tid)
        return

    # 🔔 اگر لایک تازه‌ای است، کارت کامل لایک‌کننده برای طرف مقابل بفرست
    if not already_liked:
        await _send_like_card(context, db, tid, uid)
    await q.answer("💚 لایک شد! کارت تو رفت برای طرف 🤞")
    await show_card(update, context)


async def on_buddy_cb(update, context):
    q = update.callback_query
    db = get_db(context)
    uid = q.from_user.id
    data = q.data

    if data.startswith("buddy:chat:"):
        bid = int(data.split(":")[2])
        b = db.get_buddy_of(uid, bid)
        if not b:
            await q.answer("این دوستی معتبر نیست 🤷", show_alert=True)
            return
        other = b["a_id"] if b["b_id"] == uid else b["a_id"]
        mu = db.get_user(uid)
        ou = db.get_user(other)
        if not (mu and mu["is_pro"]):
            await q.answer("💬 چت پرو مال نسخه 💎 پروه! با ادمین در تماس باش.", show_alert=True)
            return
        if not (ou and ou["is_pro"]):
            await q.answer("🥲 طرف مقابل هنوز پرو نیست!", show_alert=True)
            return
        db.set_chat_flag(bid, uid, 1)
        b = db.get_buddy(bid)
        if b["chat_a"] and b["chat_b"]:
            await q.answer("💬 چت فعال شد!")
            await notify(
                context, uid,
                "💬 <b>چت پرو فعال شد!</b>\n"
                "💌 از این به بعد پیام‌هات مستقیم می‌ره برای طرف مقابل.\n"
                "🔌 برای خاموش کردن: /chatoff",
            )
            await notify(
                context, other,
                "💬 <b>چت پرو فعال شد!</b>\n"
                "💌 طرف مقابل قبول کرد؛ پیام‌هات رو بفرست!\n"
                "🔌 برای خاموش کردن: /chatoff",
            )
        else:
            await q.answer("✅ ثبت شد!")
            await notify(context, uid, "🕊 درخواست چتت ثبت شد؛ وقتی طرف مقابل هم قبول کنه، چت روشن می‌شه!")
        return

    if data.startswith("bsize:"):
        # 🎼 مرحله ۱: اندازه انتخاب شد → حالا انتخاب سبک مشترک
        _, n_raw, bid_raw = data.split(":")
        n = int(n_raw)
        bid = int(bid_raw)
        b = db.get_buddy_of(uid, bid)
        if not b:
            await q.answer("این دوستی معتبر نیست 🤷", show_alert=True)
            return
        # 🏅 فقط کسی که زودتر لایک داده می‌تونه انتخاب کنه
        first = db.get_first_liker(b["a_id"], b["b_id"])
        if first != uid:
            await q.answer("🏅 انتخاب‌ها با کسیه که زودتر لایک داده!", show_alert=True)
            return
        other = b["a_id"] if b["b_id"] == uid else b["a_id"]
        common = _common_genres(db, uid, other)
        if common:
            await q.answer("🎼 حالا سبک رو انتخاب کن!")
            per = PLAYLIST_MODES[n]
            await notify(
                context, uid,
                f"🎧 اندازه <b>{fa(n)}تایی</b> (هر نفر {fa(per)} آهنگ) ثبت شد!\n\n"
                f"🎼 حالا از بین <b>سبک‌های مشترک شما دو نفر</b>، یه سبک انتخاب کن "
                f"تا پلی‌لیست با هم توی اون سبک بسازید:",
                genre_pick_kb(bid, n, common),
            )
        else:
            # 😌 سبک مشترکی ندارند → مستقیم بدون سبک بساز
            db.close_user_private_sessions(uid)
            db.close_user_private_sessions(other)
            await q.answer("🎧 پلی‌لیست ساخته شد!")
            await hs.start_buddy_session(update, context, uid, other, n, genre="")
        return

    if data.startswith("bgenre:"):
        # 🎼 مرحله ۲: سبک انتخاب شد → ساخت پلی‌لیست با آن سبک
        parts = data.split(":")
        if len(parts) < 4:
            await q.answer("دستور نامعتبره 🤔", show_alert=True)
            return
        idx_raw, bid_raw, n_raw = parts[1], parts[2], parts[3]
        try:
            n = int(n_raw)
            bid = int(bid_raw)
        except ValueError:
            await q.answer("دستور نامعتبره 🤔", show_alert=True)
            return
        if n not in PLAYLIST_MODES:
            await q.answer("دستور نامعتبره 🤔", show_alert=True)
            return
        b = db.get_buddy_of(uid, bid)
        if not b:
            await q.answer("این دوستی معتبر نیست 🤷", show_alert=True)
            return
        first = db.get_first_liker(b["a_id"], b["b_id"])
        if first != uid:
            await q.answer("🏅 انتخاب‌ها با کسیه که زودتر لایک داده!", show_alert=True)
            return
        other = b["a_id"] if b["b_id"] == uid else b["a_id"]
        if idx_raw == "x":
            genre = ""
        else:
            try:
                genre = GENRES[int(idx_raw)]
            except (ValueError, IndexError):
                genre = ""
        db.close_user_private_sessions(uid)
        db.close_user_private_sessions(other)
        await q.answer("🎧 پلی‌لیست ساخته شد!")
        await hs.start_buddy_session(update, context, uid, other, n, genre=genre)
        return

    await q.answer()