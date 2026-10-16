# -*- coding: utf-8 -*-
"""⌨️ کیبوردهای شیشه‌ای ربات"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from utils import fa


def main_menu(show_admin=False):
    rows = [
        [InlineKeyboardButton("🧭 اکسپلور", callback_data="menu:explore"),
         InlineKeyboardButton("🔥 محبوب‌ها", callback_data="menu:popular")],
        [InlineKeyboardButton("🎧 پلی‌لیست من", callback_data="menu:personal"),
         InlineKeyboardButton("💚 افراد لایک‌شده", callback_data="blist:open")],
        [InlineKeyboardButton("🎁 معرفی به دوستان", callback_data="ref:open"),
         InlineKeyboardButton("💎 نسخه پرو", callback_data="menu:pro")],
        [InlineKeyboardButton("👤 پروفایل من", callback_data="menu:profile"),
         InlineKeyboardButton("ℹ️ راهنما", callback_data="menu:help")],
    ]
    if show_admin:
        rows.append([InlineKeyboardButton("🛠 پنل ادمین", callback_data="ad:panel")])
    return InlineKeyboardMarkup(rows)


def back_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 منوی اصلی", callback_data="menu:main")],
    ])


def player_kb(sid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏮ قبلی", callback_data=f"pl:prev:{sid}"),
         InlineKeyboardButton("⏭ بعدی", callback_data=f"pl:next:{sid}")],
        [InlineKeyboardButton("🔁 از اول", callback_data=f"pl:restart:{sid}"),
         InlineKeyboardButton("📋 لیست", callback_data=f"pl:list:{sid}"),
         InlineKeyboardButton("⏹ پایان", callback_data=f"pl:stop:{sid}")],
    ])


def genres_kb(selected, genres):
    rows = []
    row = []
    for i, g in enumerate(genres):
        mark = "✅ " if g in selected else "▫️ "
        row.append(InlineKeyboardButton(f"{mark}{g}", callback_data=f"genre:{i}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(f"✅ ثبت ({fa(len(selected))}/۳)", callback_data="genres:done")])
    return InlineKeyboardMarkup(rows)


def explore_kb(target_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💚 دوستش دارم!", callback_data=f"ex:like:{target_id}"),
         InlineKeyboardButton("💔 رد", callback_data=f"ex:pass:{target_id}")],
        [InlineKeyboardButton("⏭ بعدی", callback_data=f"ex:skip:{target_id}"),
         InlineKeyboardButton("🔙 منوی اصلی", callback_data="menu:main")],
    ])


# 💚 کارت لایک: لایک مستقیم همان نفر بدون گشتن در اکسپلور
def like_card_kb(liker_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💚 لایکش کردم! مچ شویم 🎉", callback_data=f"ex:directlike:{liker_id}")],
        [InlineKeyboardButton("💔 نه، ردش کردم", callback_data=f"ex:directpass:{liker_id}")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="menu:main")],
    ])


# 🔒 دیوار عضویت کانال اجباری
def channel_join_kb(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📣 عضویت در کانال", url=link)],
        [InlineKeyboardButton("✅ عضو شدم، بررسی کن", callback_data="ex:chan")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="menu:main")],
    ])


# 🏅 پنل مچ برای انتخاب‌کننده (کسی که زودتر لایک داده)
def buddy_kb(bid, both_pro):
    chat_label = "💬 چت پرو 💎" if both_pro else "💬 چت (نیاز به پرو 💎)"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("2️⃣ ۲تایی (هر نفر ۱)", callback_data=f"bsize:2:{bid}"),
         InlineKeyboardButton("6️⃣ ۶تایی (هر نفر ۳)", callback_data=f"bsize:6:{bid}")],
        [InlineKeyboardButton("🔟 ۱۰تایی (هر نفر ۵)", callback_data=f"bsize:10:{bid}")],
        [InlineKeyboardButton(chat_label, callback_data=f"buddy:chat:{bid}")],
    ])


# ⏳ پنل مچ برای طرف مقابل (انتخاب سایز با لایک‌کننده اول است)
def buddy_chat_kb(bid, both_pro):
    chat_label = "💬 چت پرو 💎" if both_pro else "💬 چت (نیاز به پرو 💎)"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(chat_label, callback_data=f"buddy:chat:{bid}")],
    ])


# 🎼 انتخاب سبک مشترک برای پلی‌لیست — بعد از انتخاب اندازه
def genre_pick_kb(bid, n, common_genres):
    """دکمه‌های سبک‌های مشترک دو نفر + گزینه «بدون سبک»
    سبک‌ها با اندیس لیست GENRES فرستاده می‌شوند (bgenre:idx:bid:n)"""
    rows = []
    row = []
    for g in common_genres:
        try:
            from config import GENRES
            idx = GENRES.index(g)
        except (ValueError, ImportError):
            continue
        row.append(InlineKeyboardButton(f"🎼 {g}",
                                        callback_data=f"bgenre:{idx}:{bid}:{n}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("🎧 بدون سبک",
                                      callback_data=f"bgenre:x:{bid}:{n}")])
    return InlineKeyboardMarkup(rows)


# ---------- 💚 افراد لایک‌شده ----------
def buddy_list_kb(buddies):
    """buddies: لیستی از (other_id, name)"""
    rows = []
    for other_id, name in buddies:
        short = (name or "کاربر")[:24]
        rows.append([InlineKeyboardButton(f"👤 {short}",
                                          callback_data=f"bl:user:{other_id}")])
    rows.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def buddy_panel_kb(other_id, sessions):
    """پنل یک دوست: پلی‌لیست‌های قبلی + درخواست ساخت پلی‌لیست جدید
    sessions: لیستی از (sid, title)"""
    rows = []
    for sid, title in sessions[:10]:
        short = (title or "پلی‌لیست مشترک")[:26]
        rows.append([InlineKeyboardButton(f"🎧 {short}",
                                          callback_data=f"bl:open:{sid}")])
    rows.append([InlineKeyboardButton("🆕 ۲تایی (هر نفر ۱)",
                                      callback_data=f"bl:blsize:2:{other_id}"),
                 InlineKeyboardButton("🆕 ۶تایی (هر نفر ۳)",
                                      callback_data=f"bl:blsize:6:{other_id}")])
    rows.append([InlineKeyboardButton("🆕 ۱۰تایی (هر نفر ۵)",
                                      callback_data=f"bl:blsize:10:{other_id}")])
    rows.append([InlineKeyboardButton("🔙 افراد لایک‌شده", callback_data="blist:open"),
                 InlineKeyboardButton("🏠 منوی اصلی", callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def buddy_playlist_kb(sid, other_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎧 گوش دادن به پلی‌لیست", callback_data=f"bl:play:{sid}")],
        [InlineKeyboardButton("🔙 پنل دوست", callback_data=f"bl:back:{other_id}")],
    ])


# 🎧 درخواست ساخت پلی‌لیست جدید — برای طرف مقابل
def new_playlist_req_kb(n, requester_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ قبول می‌کنم! 🎧",
                              callback_data=f"bl:ynew:{n}:{requester_id}")],
        [InlineKeyboardButton("❌ نه، بعداً",
                              callback_data=f"bl:nnew:{n}:{requester_id}")],
    ])


# ---------- 🎁 معرفی به دوستان ----------
def share_ref_kb(bot_username, uid, ads_text):
    """دکمه اشتراک‌گذاری لینک معرفی (با پیام آماده تلگرام)"""
    from urllib.parse import quote
    link = f"https://t.me/{bot_username}?start=ref_{uid}"
    share_url = (f"https://t.me/share/url?url={quote(link)}"
                 f"&text={quote(ads_text)}")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 اشتراک‌گذاری لینک معرفی", url=share_url)],
        [InlineKeyboardButton("🔄 به‌روزرسانی شمارنده", callback_data="ref:refresh")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="menu:main")],
    ])


def profile_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ ساخت/ویرایش پروفایل", callback_data="profile:start")],
        [InlineKeyboardButton("🧭 اکسپلور", callback_data="menu:explore"),
         InlineKeyboardButton("🔥 محبوب‌ها", callback_data="menu:popular")],
        [InlineKeyboardButton("🔙 منوی اصلی", callback_data="menu:main")],
    ])


def personal_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ افزودن آهنگ", callback_data="per:add"),
         InlineKeyboardButton("▶️ پخش", callback_data="per:play")],
        [InlineKeyboardButton("🗑 حذف آهنگ", callback_data="per:del")],
        [InlineKeyboardButton("🔙 منوی اصلی", callback_data="menu:main")],
    ])


def personal_del_kb(tracks):
    rows = []
    for t in tracks[:20]:
        title = (t["title"] or "بی‌نام")[:24]
        rows.append([InlineKeyboardButton(f"🗑 {title}", callback_data=f"per:delone:{t['id']}")])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="per:back")])
    return InlineKeyboardMarkup(rows)


# ---------- 🔥 پلی‌لیست‌های محبوب ----------
def popular_list_kb(items):
    rows = []
    for sid, title, likes in items:
        short = (title or "بدون عنوان")[:28]
        rows.append([InlineKeyboardButton(
            f"❤️ {fa(likes)} | {short}",
            callback_data=f"pop:open:{sid}",
        )])
    rows.append([InlineKeyboardButton("🔄 به‌روزرسانی", callback_data="pop:refresh")])
    rows.append([InlineKeyboardButton("🔙 منوی اصلی", callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def popular_detail_kb(sid, liked):
    like_label = "💔 برداشتن لایک" if liked else "❤️ لایک"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(like_label, callback_data=f"pop:like:{sid}"),
         InlineKeyboardButton("🎧 گوش دادن", callback_data=f"pop:play:{sid}")],
        [InlineKeyboardButton("🔥 لیست محبوب‌ها", callback_data="pop:refresh")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="menu:main")],
    ])


def group_join_kb(sid, locked, is_creator):
    rows = []
    if not locked:
        rows.append([InlineKeyboardButton("✋ منم هستم!", callback_data=f"g:join:{sid}")])
        if is_creator:
            rows.append([InlineKeyboardButton("▶️ قفل و ادامه", callback_data=f"g:lock:{sid}"),
                         InlineKeyboardButton("❌ لغو", callback_data=f"g:cancel:{sid}")])
    return InlineKeyboardMarkup(rows)


# ---------- 🛠 پنل ادمین ----------
def admin_panel_kb(has_channel):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 کاربران", callback_data="ad:users:0"),
         InlineKeyboardButton("📊 آمار", callback_data="ad:stats")],
        [InlineKeyboardButton(f"📣 کانال اجباری {'✅' if has_channel else '❌'}",
                              callback_data="ad:chan"),
         InlineKeyboardButton("📢 پیام همگانی", callback_data="ad:bcast")],
        [InlineKeyboardButton("🚪 خروج", callback_data="menu:main")],
    ])


def admin_back_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 پنل ادمین", callback_data="ad:panel")],
    ])


def admin_users_kb(users, page, total_pages):
    rows = []
    row = []
    for u in users:
        name = (u["display_name"] or u["tg_name"] or str(u["user_id"]))[:16]
        marks = ("💎" if u["is_pro"] else "") + ("🚫" if u["banned"] else "")
        row.append(InlineKeyboardButton(f"👤 {marks}{name}",
                                        callback_data=f"ad:user:{u['user_id']}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"ad:users:{page - 1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(f"🔢 {fa(page + 1)}/{fa(total_pages)}",
                                        callback_data="ad:nop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"ad:users:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 پنل ادمین", callback_data="ad:panel")])
    return InlineKeyboardMarkup(rows)


def admin_user_kb(uid, is_pro, banned):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▫️ حذف پرو" if is_pro else "💎 پرو کن",
                              callback_data=f"ad:pro:{uid}"),
         InlineKeyboardButton("✅ آزادسازی" if banned else "🚫 بن کن",
                              callback_data=f"ad:ban:{uid}")],
        [InlineKeyboardButton("🔄 ریست بازدید اکسپلور", callback_data=f"ad:resetexp:{uid}"),
         InlineKeyboardButton("📩 پیام به کاربر", callback_data=f"ad:dm:{uid}")],
        [InlineKeyboardButton("🔙 لیست کاربران", callback_data="ad:users:0"),
         InlineKeyboardButton("🛠 پنل", callback_data="ad:panel")],
    ])


def admin_channel_kb(has_channel):
    label = "✏️ تغییر کانال" if has_channel else "✏️ تنظیم کانال"
    rows = [
        [InlineKeyboardButton(label, callback_data="ad:chanset")],
    ]
    if has_channel:
        rows.append([InlineKeyboardButton("🗑 حذف کانال", callback_data="ad:chandel")])
    rows.append([InlineKeyboardButton("🔙 پنل ادمین", callback_data="ad:panel")])
    return InlineKeyboardMarkup(rows)


def broadcast_confirm_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ارسال به همه", callback_data="bc:yes"),
         InlineKeyboardButton("❌ لغو", callback_data="bc:no")],
    ])