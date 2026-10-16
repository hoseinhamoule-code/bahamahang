# -*- coding: utf-8 -*-
"""🧭 منوی اصلی، راهنما، پروفایل، معرفی به دوستان، بن و دستورهای ادمین"""

import json

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS, BOT_NAME, GENRES, MAX_GENRES, MAX_SINGERS
from keyboards import (back_main, genres_kb, main_menu, profile_kb,
                       share_ref_kb)
from utils import (BANNED_TEXT, edit_or_send, esc, fa, get_db, maybe_relay,
                   notify, parse_list)
import handlers_admin as ha
import handlers_explore as he
import handlers_session as hs

# 🎁 تعداد معرفی لازم برای فعال‌سازی خودکار نسخه پرو
REF_REWARD = 5

WELCOME = f"""🎧 <b>به «{BOT_NAME}» خوش اومدی!</b>

🎶 این‌جا با آدم‌های هم‌سلیقه مچ می‌شی، با هم پلی‌لیست مشترک می‌سازید و آهنگ‌ها <b>یکی‌درمیون</b> پخش می‌شه!

🧭 <b>اکسپلور:</b> آدم‌های هم‌سلیقه رو پیدا کن؛ بعد از مچ 💚 پلی‌لیست مشترک بسازید!
🔥 <b>محبوب‌ها:</b> پلی‌لیست‌های ساخته‌شده بقیه رو ببین، لایک کن ❤️ و گوش بده!
💚 <b>افراد لایک‌شده:</b> دوستان مچ‌شده‌ات و پلی‌لیست‌های مشترکتون همیشه دستت باشه!
🎁 <b>معرفی:</b> ۵ نفر رو دعوت کن و نسخه پرو رایگان بگیر!
🎧 <b>پلی‌لیست من:</b> یه پلی‌لیست شخصی توی پروفایلت داشته باش!
👥 <b>گروهی:</b> ربات رو به گروهت اضافه کن و /start بزن — تا ۵ نفر با هم پلی‌لیست می‌سازن!
💎 <b>نسخه پرو:</b> بعد از مچ، با طرف مقابل‌ت چت کن!

⬇️ از منوی زیر انتخاب کن:"""

HELP = """ℹ️ <b>راهنمای کامل</b>

🧭 <b>اکسپلور و پلی‌لیست مشترک</b>
۱. اول پروفایلت رو کامل کن (اسم، شهر، سن، عکس، سبک‌ها، خواننده‌ها).
۲. نفرات جدید اول نمایش داده می‌شن و بعد نفراتی که قبلاً دیده‌ای (با برچسب «👁 قبلا دیده شده»).
۳. 🎯 ۱۰ نفر اول رایگانه؛ برای هر ۵ نفر بعدی باید عضو کانال رسمی ربات بشی 📣
۴. لایک کن؛ اگه طرف هم لایکت کرد → مچ! 🎉 بعد از مچ، کسی که زودتر لایک داده تعداد آهنگ‌ها رو انتخاب می‌کنه (۲تایی/۶تایی/۱۰تایی).
۵. هر دو نفر آهنگ‌هاتون رو بفرستید (mp3)؛ پلی‌لیست یکی‌درمیون پخش می‌شه! 🎧

💚 <b>افراد لایک‌شده</b>
همه کسایی که باهاشون مچ شدی اینجاست؛ می‌تونی پلی‌لیست‌های قبلی مشترکتون رو ببینی و گوش بدی، یا درخواست پلی‌لیست جدید بدی!

🎁 <b>معرفی به دوستان</b>
لینک معرفت رو برای دوستات بفرست؛ به‌ازای هر نفر که با لینک تو عضو ربات شه، شمارنده‌ت بالا می‌ره.
🏆 با <b>۵ معرفی</b>، نسخه <b>پرو</b> 💎 به‌صورت خودکار و رایگان برات فعال می‌شه!

🔥 <b>پلی‌لیست‌های محبوب</b>
پلی‌لیست‌هایی که توی اکسپلور ساخته می‌شن، اینجا بر اساس تعداد لایک مرتب می‌شن! ❤️

💬 <b>چت پرو (نسخه 💎)</b>
بعد از مچ، اگر هر دوتون پرو باشید و چت رو فعال کنید، پیام‌هاتون مستقیم می‌ره برای طرف مقابل.

👥 <b>حالت گروهی</b>
۱. ربات رو به گروه اضافه کن (حالت Privacy رو از BotFather خاموش کن!).
۲. توی گروه /start یا /music بزن.
۳. تا ۵ نفر با دکمه «✋ منم هستم» میان تو؛ هر کس ۲ آهنگ می‌فرسته و پخش گروهی شروع می‌شه!

🎧 <b>پلی‌لیست من</b>
توی پروفایلت یه پلی‌لیست شخصی داری؛ هر وقت خواستی آهنگ اضافه کن و گوش بده.

👤 <b>پروفایل</b>
اسم، شهر، سن، عکس، حداکثر ۳ سبک محبوب از لیست ۲۰تایی و ۳ خواننده محبوب.

⌨️ <b>دستورها:</b>
/start — شروع • /help — راهنما • /done — پایان حالت افزودن آهنگ • /chatoff — خاموش کردن چت پرو"""

PRO_TEXT = """💎 <b>نسخه پرو</b>

با نسخه پرو، بعد از مچ شدن توی اکسپلور 🧭 می‌تونی با طرف مقابل <b>چت کنی</b> 💌
(نسخه معمولی فقط می‌تونه آهنگ بفرسته 🎵)

{status}

🔑 برای فعال‌سازی پرو با ادمین ربات در تماس باش، یا ۵ نفر رو با لینک معرفی‌ات دعوت کن! 🎁"""


def _menu_for(uid):
    """منوی اصلی — برای ادمین دکمه پنل هم دارد"""
    return main_menu(uid in ADMIN_IDS)


# ---------- 🎁 معرفی به دوستان ----------
async def ref_panel(update, context):
    """🎁 نمایش پنل معرفی با لینک، پیام تبلیغاتی و شمارنده"""
    db = get_db(context)
    uid = update.callback_query.from_user.id
    me = await context.bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{uid}"
    ads_text = (
        "🎧 «نوبت منه آهنگ بزارم» رو امتحان کن!\n\n"
        "🧭 با هر کسی که سلیقه‌اش به تو بخوره مچ می‌شی، پلی‌لیست مشترک می‌سازید "
        "و آهنگ‌ها یکی‌درمیون پخش می‌شن!\n"
        "👤 می‌تونی پروفایل بسازی و مشخصاتت رو اضافه کنی: شهر، سن، سبک‌های محبوب و خواننده‌هات!\n"
        "🔥 پلی‌لیست‌هات توی بخش «محبوب‌ها» قرار می‌گیره و بقیه لایکشون می‌کنن!\n"
        "🎁 با معرفی ۵ دوست، نسخه پرو 💎 رایگان می‌شه!\n\n"
        "👇 همین الان عضو شو:"
    )
    cnt = db.referral_count(uid)
    u = db.get_user(uid)
    pro_state = ("💎 <b>جایزه‌ات اومده! نسخه پرو فعاله ✅</b>"
                 if u and u["is_pro"]
                 else f"🏆 {fa(cnt)} از {fa(REF_REWARD)} معرفی")
    text = (
        "🎁 <b>معرفی به دوستان</b>\n\n"
        "🔗 لینک معرفی اختصاصی‌ات:\n"
        f"{link}\n\n"
        f"👥 تا حالا <b>{fa(cnt)} نفر</b> با لینک تو عضو ربات شدن.\n"
        f"{pro_state}\n\n"
        "💎 <b>جایزه:</b> با معرفی <b>۵ نفر</b>، نسخه پرو (چت با طرف مقابل بعد از مچ 💬) "
        "به‌صورت خودکار و رایگان برات فعال می‌شه!\n\n"
        "📤 با دکمه پایین، لینک رو همراه پیام تبلیغاتی برای دوستات بفرست:"
    )
    await edit_or_send(update, context, text,
                       share_ref_kb(me.username, uid, ads_text))


async def on_ref_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("🎁")
    await ref_panel(update, context)


# ---------- شروع و منو ----------
async def cmd_start_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    u = update.effective_user

    # 🎁 پردازش لینک معرفی — قبل از ثبت کاربر، تا «جدید بودن» مشخص شود
    referrer_id = 0
    if context.args:
        arg = context.args[0]
        if arg.startswith("ref_"):
            try:
                referrer_id = int(arg[4:])
            except ValueError:
                referrer_id = 0
            if referrer_id == u.id:
                referrer_id = 0
        elif arg.startswith("join_"):
            await update.message.reply_html(
                "ℹ️ <b>پلی‌لیست دونفره با لینک دعوت حذف شد!</b>\n\n"
                "🧭 حالا برای ساخت پلی‌لیست مشترک، از <b>اکسپلور</b> استفاده کن: "
                "پروفایلت رو بساز، هم‌سلیقه‌هات رو پیدا کن و بعد از مچ، "
                "پلی‌لیست مشترک بسازید! 🎧",
                reply_markup=_menu_for(u.id),
            )
            return

    is_new_user = db.get_user(u.id) is None
    db.upsert_user(u.id, u.username or "", u.full_name or "")

    if referrer_id and is_new_user:
        added = db.add_referral(referrer_id, u.id)
        if added:
            db.bump_invites(referrer_id)
            cnt = db.referral_count(referrer_id)
            r = db.get_user(referrer_id)
            if cnt >= REF_REWARD and r and not r["is_pro"]:
                db.set_user_fields(referrer_id, is_pro=1)
                await notify(
                    context, referrer_id,
                    "🎉🎉🎉 <b>تبریک!</b>\n"
                    f"<b>{fa(REF_REWARD)} نفر</b> رو با لینک معرفی‌ات به ربات آوردی و "
                    "<b>نسخه پرو 💎</b> به‌صورت رایگان فعال شد!\n\n"
                    "💬 حالا بعد از مچ می‌تونی با طرف مقابل‌ت چت کنی!",
                )
            else:
                await notify(
                    context, referrer_id,
                    f"🎁 <b>{esc(u.first_name or 'یه نفر جدید')}</b> با لینک تو به ربات اومد! 🥳\n"
                    f"👥 معرفی‌ها: <b>{fa(cnt)} از {fa(REF_REWARD)}</b>\n\n"
                    + ("💎 با معرفی <b>۵ نفر</b>، نسخه پرو رایگان فعال می‌شه!"
                       if r and not r["is_pro"] else "💎 تو که پرو هستی؛ دمت گرم! 🔥"),
                )

    if db.is_banned(u.id):
        await update.message.reply_html(BANNED_TEXT)
        return

    await update.message.reply_html(WELCOME, reply_markup=_menu_for(u.id))


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(HELP, reply_markup=_menu_for(update.effective_user.id))


async def on_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = get_db(context)
    uid = q.from_user.id
    data = q.data
    await q.answer()

    if db.is_banned(uid):
        await edit_or_send(update, context, BANNED_TEXT, back_main())
        return

    if data == "menu:main":
        context.user_data.pop("flow", None)
        context.user_data.pop("pf", None)
        context.user_data.pop("admin_flow", None)
        await edit_or_send(update, context, WELCOME, _menu_for(uid))
    elif data == "menu:popular":
        await hs.popular_panel(update, context)
    elif data == "menu:help":
        await edit_or_send(update, context, HELP, back_main())
    elif data == "menu:pro":
        uu = db.get_user(uid)
        status = "✅ تو عضو نسخه پرو هستی!" if (uu and uu["is_pro"]) else "❌ فعلاً پرو نیستی."
        await edit_or_send(update, context, PRO_TEXT.format(status=status), back_main())
    elif data == "menu:profile":
        await show_profile(update, context)
    elif data == "menu:explore":
        await he.explore_open(update, context)
    elif data == "menu:personal":
        await hs.personal_panel(update, context)


# ---------- پروفایل ----------
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    uid = update.callback_query.from_user.id
    u = db.get_user(uid)
    if not db.profile_ready(u):
        await edit_or_send(
            update, context,
            "👤 <b>پروفایلت هنوز خالیه!</b>\n\nبرای اکسپلور 🧭 و مچ شدن باید پروفایلت رو بسازی:\n"
            "اسم، شهر، سن، عکس، سبک‌های محبوب و خواننده‌ها 🎶",
            profile_kb(),
        )
        return
    genres = ", ".join(json.loads(u["genres"] or "[]")) or "—"
    singers = ", ".join(json.loads(u["singers"] or "[]")) or "—"
    text = (
        "👤 <b>پروفایل من</b>\n\n"
        f"👤 اسم: <b>{esc(u['display_name'])}</b>\n"
        f"🏙 شهر: {esc(u['city']) or '—'}\n"
        f"🎂 سن: {fa(u['age'])}\n"
        f"🎼 سبک‌ها: {esc(genres)}\n"
        f"🎤 خواننده‌های محبوب: {esc(singers)}\n"
        f"💎 {'پرو ✅' if u['is_pro'] else 'معمولی'}"
    )
    await edit_or_send(update, context, text, profile_kb())


async def on_profile_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = get_db(context)
    uid = q.from_user.id
    data = q.data

    if data == "profile:start":
        await q.answer()
        u = db.get_user(uid)
        pf = context.user_data.setdefault("pf", {})
        pf["genres"] = []
        pf["photo"] = ""
        if u:
            pf["name"] = u["display_name"] or ""
            pf["age"] = u["age"] or 0
            pf["city"] = u["city"] or ""
        context.user_data["flow"] = "pf:name"
        await edit_or_send(
            update, context,
            "👤 <b>ساخت پروفایل</b> — مرحله ۱ از ۶\n\n"
            "۱️⃣ اسمی که می‌خوای بقیه ببینن چیه؟\n(مثلاً: علی)",
            back_main(),
        )
        return

    if data.startswith("genre:"):
        pf = context.user_data.get("pf", {})
        sel = pf.setdefault("genres", [])
        g = GENRES[int(data.split(":")[1])]
        if g in sel:
            sel.remove(g)
            await q.answer(f"حذف شد: {g}")
        elif len(sel) < MAX_GENRES:
            sel.append(g)
            await q.answer(f"اضافه شد: {g}")
        else:
            await q.answer(f"حداکثر {fa(MAX_GENRES)} سبک می‌تونی انتخاب کنی! 🙅", show_alert=True)
        try:
            await q.edit_message_reply_markup(reply_markup=genres_kb(sel, GENRES))
        except Exception:
            pass
        return

    if data == "genres:done":
        pf = context.user_data.get("pf", {})
        sel = pf.get("genres", [])
        if not sel:
            await q.answer("حداقل یه سبک انتخاب کن! 🎶", show_alert=True)
            return
        await q.answer()
        context.user_data["flow"] = "pf:singers"
        chosen = "\n".join(f"▫️ {esc(s)}" for s in sel)
        await edit_or_send(
            update, context,
            f"عالی! ✅ سبک‌های انتخابی:\n{chosen}\n\n"
            "۶️⃣ حالا اسم <b>۳ خواننده محبوبت</b> رو با ویرگول بنویس 🎤\n"
            "(مثلاً: محسن چاوشی، سیروان خسروی، ابی)",
            back_main(),
        )
        return

    await q.answer()


async def handle_profile_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """مراحل متنی ساخت پروفایل — اگر پیام مال پروفایل بود True برمی‌گرداند"""
    flow = context.user_data.get("flow")
    if not flow:
        return False
    db = get_db(context)
    uid = update.effective_user.id
    text = (update.message.text or "").strip()
    pf = context.user_data.setdefault("pf", {})

    if flow == "pf:name":
        if len(text) < 2 or len(text) > 40:
            await update.message.reply_text("اسم رو بین ۲ تا ۴۰ حرف بنویس 🙏")
            return True
        pf["name"] = text
        context.user_data["flow"] = "pf:age"
        await update.message.reply_html("۲️⃣ چند سالته؟ 🎂\n(یه عدد بین ۱۰ تا ۹۹ بنویس)")
        return True

    if flow == "pf:age":
        if not text.isdigit() or not (10 <= int(text) <= 99):
            await update.message.reply_text("یه عدد بین ۱۰ تا ۹۹ بفرست 🎂")
            return True
        pf["age"] = int(text)
        context.user_data["flow"] = "pf:city"
        await update.message.reply_html("۳️⃣ شهرت چیه؟ 🏙\n(مثلاً: تهران)")
        return True

    if flow == "pf:city":
        if len(text) < 2 or len(text) > 40:
            await update.message.reply_text("اسم شهر رو بین ۲ تا ۴۰ حرف بنویس 🏙")
            return True
        pf["city"] = text
        context.user_data["flow"] = "pf:photo"
        await update.message.reply_html(
            "۴️⃣ یه عکس پروفایل بفرست 📸\nاگه نمی‌خوای، فقط بنویس: ⏭ رد شدن"
        )
        return True

    if flow == "pf:photo":
        if "رد" in text:
            context.user_data["flow"] = "pf:genres"
            await update.message.reply_html(
                "۵️⃣ از لیست زیر <b>حداکثر ۳ سبک محبوب</b> رو انتخاب کن 🎼",
                reply_markup=genres_kb(pf.setdefault("genres", []), GENRES),
            )
            return True
        await update.message.reply_text("عکس بفرست 📸 یا بنویس: ⏭ رد شدن")
        return True

    if flow == "pf:genres":
        await update.message.reply_html(
            "🎼 لطفاً سبک‌ها رو با دکمه‌های زیر انتخاب کن (حداکثر ۳ تا):",
            reply_markup=genres_kb(pf.setdefault("genres", []), GENRES),
        )
        return True

    if flow == "pf:singers":
        singers = parse_list(text, MAX_SINGERS)
        if not singers:
            await update.message.reply_text("حداقل اسم یه خواننده رو بنویس 🎤")
            return True
        db.upsert_user(uid, update.effective_user.username or "",
                       update.effective_user.full_name or "")
        db.set_user_fields(
            uid,
            display_name=pf.get("name", ""),
            age=pf.get("age", 0),
            city=pf.get("city", ""),
            photo_file_id=pf.get("photo", ""),
            genres=json.dumps(pf.get("genres", []), ensure_ascii=False),
            singers=json.dumps(singers, ensure_ascii=False),
        )
        context.user_data.pop("flow", None)
        context.user_data.pop("pf", None)
        await update.message.reply_html(
            "🎉 <b>پروفایلت ساخته شد!</b>\n\n"
            "حالا برو اکسپلور و آدم‌های هم‌سلیقه رو پیدا کن! 🧭💚",
            reply_markup=_menu_for(uid),
        )
        return True

    return False


# ---------- پیام‌های خصوصی ----------
async def on_private_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    u = update.effective_user
    db.upsert_user(u.id, u.username or "", u.full_name or "")
    if db.is_banned(u.id):
        await update.message.reply_html(BANNED_TEXT)
        return
    if await ha.handle_admin_text(update, context):
        return
    if await handle_profile_text(update, context):
        return
    if context.user_data.get("personal_add"):
        await update.message.reply_html(
            "🎵 برای افزودن به <b>پلی‌لیست شخصی</b>، فایل آهنگ (mp3) بفرست.\n"
            "✅ برای پایان: /done"
        )
        return
    if await maybe_relay(update, context):
        return
    await update.message.reply_html(
        "🤔 متوجه نشدم! از منوی زیر استفاده کن یا /help بزن:",
        reply_markup=_menu_for(u.id),
    )


async def on_private_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    db = get_db(context)
    if db.is_banned(update.effective_user.id):
        await msg.reply_html(BANNED_TEXT)
        return
    flow = context.user_data.get("flow")
    if flow == "pf:photo":
        if msg.photo:
            pf = context.user_data.setdefault("pf", {})
            pf["photo"] = msg.photo[-1].file_id
            context.user_data["flow"] = "pf:genres"
            await msg.reply_html(
                "📸 عکس ذخیره شد!\n\n۵️⃣ حالا حداکثر ۳ سبک محبوب رو انتخاب کن 🎼",
                reply_markup=genres_kb(pf.setdefault("genres", []), GENRES),
            )
        else:
            await msg.reply_text("عکس بفرست 📸 یا بنویس: ⏭ رد شدن")
        return
    if await maybe_relay(update, context):
        return


# ---------- دستورهای دیگر ----------
async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("personal_add", None)
    context.user_data.pop("flow", None)
    context.user_data.pop("admin_flow", None)
    await update.message.reply_html("✅ باشه! حالت افزودن آهنگ بسته شد.",
                                    reply_markup=_menu_for(update.effective_user.id))


async def cmd_chatoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    uid = update.effective_user.id
    b = db.get_active_chat_buddy(uid)
    if not b:
        await update.message.reply_text("💬 چت فعالی نداری.")
        return
    db.set_chat_flag(b["id"], uid, 0)
    other = b["a_id"] if b["b_id"] == uid else b["a_id"]
    await update.message.reply_text("💤 چت پرو خاموش شد.")
    await notify(context, other, "💤 طرف مقابل چت پرو رو خاموش کرد.")


def _is_admin(uid) -> bool:
    return uid in ADMIN_IDS


async def cmd_addpro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        return
    db = get_db(context)
    target = None
    if context.args:
        try:
            target = int(context.args[0])
        except ValueError:
            target = None
    if not target and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
    if not target:
        await update.message.reply_text("استفاده: /addpro آیدی_عددی یا روی پیام کاربر ریپلای کن")
        return
    db.upsert_user(target)
    db.set_user_fields(target, is_pro=1)
    await update.message.reply_html(f"💎 کاربر <code>{target}</code> پرو شد!")
    await notify(context, target, "🎉 تبریک! عضو نسخه <b>پرو</b> شدی؛ حالا بعد از مچ می‌تونی چت کنی! 💬")


async def cmd_rmpro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        return
    db = get_db(context)
    target = None
    if context.args:
        try:
            target = int(context.args[0])
        except ValueError:
            target = None
    if not target and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
    if not target:
        await update.message.reply_text("استفاده: /rmpro آیدی_عددی یا ریپلای")
        return
    db.set_user_fields(target, is_pro=0)
    await update.message.reply_html(f"▫️ پرو کاربر <code>{target}</code> حذف شد.")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        return
    db = get_db(context)
    s = db.admin_stats()
    await update.message.reply_html(
        "📊 <b>آمار ربات</b>\n\n"
        f"👥 کاربران: {fa(s['users'])}\n"
        f"💎 پرو: {fa(s['pro'])} | 🚫 بن: {fa(s['banned'])}\n"
        f"🎧 جلسات پلی‌لیست: {fa(s['sessions'])}\n"
        f"🎵 آهنگ‌های مشترک: {fa(s['tracks'])}\n"
        f"💚 مچ‌ها: {fa(s['buddies'])}\n"
        f"❤️ لایک پلی‌لیست‌ها: {fa(s['likes'])}\n"
        f"🎁 معرفی‌های موفق: {fa(s['referrals'])}"
    )