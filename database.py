# -*- coding: utf-8 -*-
"""💾 لایه دیتابیس SQLite ربات «نوبت منه آهنگ بزارم»"""

import sqlite3
import threading

from config import DB_PATH


class Database:
    def __init__(self, path: str = DB_PATH):
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    # ---------- پایه ----------
    def _exec(self, sql, params=()):
        with self._lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return cur

    def _all(self, sql, params=()):
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def _one(self, sql, params=()):
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    # ---------- جداول ----------
    def _create_tables(self):
        self._exec("""CREATE TABLE IF NOT EXISTS users (
            user_id          INTEGER PRIMARY KEY,
            username         TEXT DEFAULT '',
            tg_name          TEXT DEFAULT '',
            display_name     TEXT DEFAULT '',
            age              INTEGER DEFAULT 0,
            city             TEXT DEFAULT '',
            photo_file_id    TEXT DEFAULT '',
            genres           TEXT DEFAULT '[]',
            singers          TEXT DEFAULT '[]',
            is_pro           INTEGER DEFAULT 0,
            banned           INTEGER DEFAULT 0,
            invites          INTEGER DEFAULT 0,
            explore_views    INTEGER DEFAULT 0,
            explore_unlocked INTEGER DEFAULT 0,
            created_at       TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        self._exec("""CREATE TABLE IF NOT EXISTS sessions (
            session_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            kind          TEXT DEFAULT 'private',
            size          INTEGER DEFAULT 0,
            per_user      INTEGER DEFAULT 0,
            creator_id    INTEGER DEFAULT 0,
            chat_id       INTEGER DEFAULT 0,
            locked        INTEGER DEFAULT 0,
            state         TEXT DEFAULT 'uploading',
            current_index INTEGER DEFAULT 0,
            title         TEXT DEFAULT '',
            genre         TEXT DEFAULT '',
            public        INTEGER DEFAULT 0,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        self._exec("""CREATE TABLE IF NOT EXISTS session_members (
            session_id INTEGER,
            user_id    INTEGER,
            uploads    INTEGER DEFAULT 0,
            PRIMARY KEY (session_id, user_id)
        )""")
        self._exec("""CREATE TABLE IF NOT EXISTS session_tracks (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            user_id    INTEGER,
            file_id    TEXT,
            title      TEXT DEFAULT '',
            performer  TEXT DEFAULT '',
            duration   INTEGER DEFAULT 0,
            slot       INTEGER
        )""")
        self._exec("""CREATE TABLE IF NOT EXISTS personal_tracks (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER,
            file_id   TEXT,
            title     TEXT DEFAULT '',
            performer TEXT DEFAULT '',
            duration  INTEGER DEFAULT 0
        )""")
        self._exec("""CREATE TABLE IF NOT EXISTS swipes (
            swiper_id  INTEGER,
            target_id  INTEGER,
            action     TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (swiper_id, target_id)
        )""")
        self._exec("""CREATE TABLE IF NOT EXISTS buddies (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            a_id       INTEGER,
            b_id       INTEGER,
            chat_a     INTEGER DEFAULT 0,
            chat_b     INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        self._exec("""CREATE TABLE IF NOT EXISTS playlist_likes (
            playlist_id INTEGER,
            user_id     INTEGER,
            PRIMARY KEY (playlist_id, user_id)
        )""")
        self._exec("""CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER,
            invited_id  INTEGER,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (referrer_id, invited_id)
        )""")
        self._exec("""CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        )""")
        self._migrate()

    def _migrate(self):
        """🔄 دیتابیس‌های قدیمی را با ستون‌های جدید به‌روز می‌کند"""
        ucols = [r["name"] for r in self._all("PRAGMA table_info(users)")]
        for col, ddl in (
            ("banned", "INTEGER DEFAULT 0"),
            ("invites", "INTEGER DEFAULT 0"),
            ("explore_views", "INTEGER DEFAULT 0"),
            ("explore_unlocked", "INTEGER DEFAULT 0"),
        ):
            if col not in ucols:
                self._exec(f"ALTER TABLE users ADD COLUMN {col} {ddl}")
        scols = [r["name"] for r in self._all("PRAGMA table_info(sessions)")]
        if "title" not in scols:
            self._exec("ALTER TABLE sessions ADD COLUMN title TEXT DEFAULT ''")
        if "genre" not in scols:
            self._exec("ALTER TABLE sessions ADD COLUMN genre TEXT DEFAULT ''")
        if "public" not in scols:
            self._exec("ALTER TABLE sessions ADD COLUMN public INTEGER DEFAULT 0")
        wcols = [r["name"] for r in self._all("PRAGMA table_info(swipes)")]
        if "created_at" not in wcols:
            self._exec("ALTER TABLE swipes ADD COLUMN created_at TEXT")

    # ---------- تنظیمات ----------
    def get_setting(self, key, default=""):
        r = self._one("SELECT value FROM settings WHERE key = ?", (key,))
        return r["value"] if r else default

    def set_setting(self, key, value):
        self._exec(
            """INSERT INTO settings (key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
            (key, value),
        )

    # ---------- کاربران ----------
    def upsert_user(self, user_id, username="", tg_name=""):
        self._exec(
            """INSERT INTO users (user_id, username, tg_name) VALUES (?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   username = excluded.username, tg_name = excluded.tg_name""",
            (user_id, username or "", tg_name or ""),
        )

    def get_user(self, user_id):
        return self._one("SELECT * FROM users WHERE user_id = ?", (user_id,))

    def set_user_fields(self, user_id, **kw):
        allowed = {"username", "tg_name", "display_name", "age", "city",
                   "photo_file_id", "genres", "singers", "is_pro", "banned",
                   "invites"}
        sets, params = [], []
        for k, v in kw.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                params.append(v)
        if not sets:
            return
        params.append(user_id)
        self._exec(f"UPDATE users SET {', '.join(sets)} WHERE user_id = ?", tuple(params))

    def count_users(self):
        r = self._one("SELECT COUNT(*) AS c FROM users")
        return r["c"] if r else 0

    def all_users(self, page, per_page):
        return self._all(
            "SELECT * FROM users ORDER BY created_at DESC, user_id DESC LIMIT ? OFFSET ?",
            (per_page, page * per_page),
        )

    def all_user_ids(self):
        return [r["user_id"] for r in self._all("SELECT user_id FROM users")]

    def is_banned(self, user_id) -> bool:
        u = self.get_user(user_id)
        return bool(u and u["banned"])

    def profile_ready(self, user) -> bool:
        if not user:
            return False
        return bool(user["display_name"]) and user["genres"] not in (None, "", "[]")

    # ---------- 🎁 معرفی به دوستان ----------
    def add_referral(self, referrer_id, invited_id) -> bool:
        """ثبت معرفی؛ اگر تازه باشد True برمی‌گرداند"""
        cur = self._exec(
            "INSERT OR IGNORE INTO referrals (referrer_id, invited_id) VALUES (?, ?)",
            (referrer_id, invited_id),
        )
        return cur.rowcount > 0

    def referral_count(self, user_id) -> int:
        r = self._one(
            "SELECT COUNT(*) AS c FROM referrals WHERE referrer_id = ?",
            (user_id,),
        )
        return r["c"] if r else 0

    def bump_invites(self, user_id):
        self._exec(
            "UPDATE users SET invites = invites + 1 WHERE user_id = ?",
            (user_id,),
        )

    # ---------- اکسپلور ----------
    def explore_new_users(self, user_id, limit=60):
        """🆕 کاربرانی که این کاربر هرگز ندیده است"""
        return self._all(
            """SELECT * FROM users
               WHERE user_id != ?
                 AND banned = 0
                 AND display_name != ''
                 AND genres != '[]'
                 AND user_id NOT IN (SELECT target_id FROM swipes WHERE swiper_id = ?)
                 AND user_id NOT IN (SELECT a_id FROM buddies WHERE b_id = ?)
                 AND user_id NOT IN (SELECT b_id FROM buddies WHERE a_id = ?)
               ORDER BY RANDOM() LIMIT ?""",
            (user_id, user_id, user_id, user_id, limit),
        )

    def explore_seen_users(self, user_id, limit=60):
        """👁 کاربرانی که قبلاً دیده و رد شده‌اند (قدیمی‌ترین اول)"""
        return self._all(
            """SELECT u.* FROM users u
               JOIN swipes s ON s.swiper_id = ? AND s.target_id = u.user_id
               WHERE s.action = 'pass'
                 AND u.user_id != ?
                 AND u.banned = 0
                 AND u.display_name != ''
                 AND u.genres != '[]'
               ORDER BY s.created_at ASC
               LIMIT ?""",
            (user_id, user_id, limit),
        )

    def inc_explore_views(self, user_id):
        self._exec(
            "UPDATE users SET explore_views = explore_views + 1 WHERE user_id = ?",
            (user_id,),
        )

    def unlock_explore_views(self, user_id, n):
        self._exec(
            "UPDATE users SET explore_unlocked = explore_unlocked + ? WHERE user_id = ?",
            (n, user_id),
        )

    def reset_explore_views(self, user_id):
        self._exec(
            "UPDATE users SET explore_views = 0 WHERE user_id = ?",
            (user_id,),
        )

    def add_swipe(self, swiper_id, target_id, action):
        self._exec(
            """INSERT INTO swipes (swiper_id, target_id, action, created_at)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(swiper_id, target_id) DO UPDATE SET
                   action = excluded.action, created_at = excluded.created_at""",
            (swiper_id, target_id, action),
        )

    def get_swipe(self, swiper_id, target_id):
        return self._one(
            "SELECT * FROM swipes WHERE swiper_id = ? AND target_id = ?",
            (swiper_id, target_id),
        )

    def get_first_liker(self, a_id, b_id):
        """👤 آی‌دی کسی که زودتر لایک داده را برمی‌گرداند (a یا b)"""
        ra = self._one(
            "SELECT created_at FROM swipes WHERE swiper_id = ? AND target_id = ?",
            (a_id, b_id),
        )
        rb = self._one(
            "SELECT created_at FROM swipes WHERE swiper_id = ? AND target_id = ?",
            (b_id, a_id),
        )
        ta = (ra["created_at"] if ra else None) or ""
        tb = (rb["created_at"] if rb else None) or ""
        if ta and tb:
            return a_id if str(ta) <= str(tb) else b_id
        if tb:
            return a_id
        return b_id

    # ---------- دوستی‌ها ----------
    def create_buddy(self, a_id, b_id):
        cur = self._exec("INSERT INTO buddies (a_id, b_id) VALUES (?, ?)", (a_id, b_id))
        return cur.lastrowid

    def get_buddy(self, bid):
        return self._one("SELECT * FROM buddies WHERE id = ?", (bid,))

    def get_buddy_between(self, a_id, b_id):
        return self._one(
            """SELECT * FROM buddies
               WHERE (a_id = ? AND b_id = ?) OR (a_id = ? AND b_id = ?)""",
            (a_id, b_id, b_id, a_id),
        )

    def list_buddies(self, user_id):
        """💚 همه دوستان مچ‌شده کاربر به‌همراه نام نمایشی طرف مقابل"""
        return self._all(
            """SELECT b.id AS bid,
                      b.created_at,
                      CASE WHEN b.a_id = :uid THEN b.b_id ELSE b.a_id END AS other_id,
                      u.display_name, u.tg_name
               FROM buddies b
               LEFT JOIN users u
                 ON u.user_id = (CASE WHEN b.a_id = :uid THEN b.b_id ELSE b.a_id END)
               WHERE b.a_id = :uid OR b.b_id = :uid
               ORDER BY b.created_at DESC, b.id DESC""",
            {"uid": user_id},
        )

    def buddy_sessions(self, a_id, b_id):
        """🎧 پلی‌لیست‌های مشترکِ ساخته‌شده بین دو نفر (از جدیدترین)"""
        return self._all(
            """SELECT s.* FROM sessions s
               WHERE s.kind = 'private'
                 AND s.state IN ('playing', 'done')
                 AND s.public = 1
                 AND EXISTS (SELECT 1 FROM session_members m
                             WHERE m.session_id = s.session_id AND m.user_id = ?)
                 AND EXISTS (SELECT 1 FROM session_members m
                             WHERE m.session_id = s.session_id AND m.user_id = ?)
               ORDER BY s.session_id DESC""",
            (a_id, b_id),
        )

    def get_buddy_of(self, user_id, bid):
        return self._one(
            "SELECT * FROM buddies WHERE id = ? AND (a_id = ? OR b_id = ?)",
            (bid, user_id, user_id),
        )

    def set_chat_flag(self, bid, user_id, val):
        b = self.get_buddy(bid)
        if not b:
            return
        col = "chat_a" if b["a_id"] == user_id else "chat_b"
        self._exec(f"UPDATE buddies SET {col} = ? WHERE id = ?", (val, bid))

    def get_active_chat_buddy(self, user_id):
        return self._one(
            """SELECT * FROM buddies
               WHERE (a_id = ? OR b_id = ?) AND chat_a = 1 AND chat_b = 1
               LIMIT 1""",
            (user_id, user_id),
        )

    # ---------- جلسات پلی‌لیست ----------
    def create_session(self, kind, size, per_user, creator_id, chat_id=0):
        cur = self._exec(
            "INSERT INTO sessions (kind, size, per_user, creator_id, chat_id) VALUES (?, ?, ?, ?, ?)",
            (kind, size, per_user, creator_id, chat_id),
        )
        return cur.lastrowid

    def get_session(self, sid):
        return self._one("SELECT * FROM sessions WHERE session_id = ?", (sid,))

    def set_session_fields(self, sid, **kw):
        allowed = {"state", "current_index", "locked", "title", "genre", "public"}
        sets, params = [], []
        for k, v in kw.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                params.append(v)
        if not sets:
            return
        params.append(sid)
        self._exec(f"UPDATE sessions SET {', '.join(sets)} WHERE session_id = ?", tuple(params))

    def add_member(self, sid, user_id) -> bool:
        cur = self._exec(
            "INSERT OR IGNORE INTO session_members (session_id, user_id) VALUES (?, ?)",
            (sid, user_id),
        )
        return cur.rowcount > 0

    def is_member(self, sid, user_id) -> bool:
        return self._one(
            "SELECT 1 AS x FROM session_members WHERE session_id = ? AND user_id = ?",
            (sid, user_id),
        ) is not None

    def get_members(self, sid):
        rows = self._all(
            "SELECT user_id FROM session_members WHERE session_id = ? ORDER BY rowid",
            (sid,),
        )
        return [r["user_id"] for r in rows]

    def member_names(self, sid):
        return self._all(
            """SELECT m.user_id AS user_id,
                      COALESCE(NULLIF(u.display_name, ''), u.tg_name, '') AS name
               FROM session_members m
               LEFT JOIN users u ON u.user_id = m.user_id
               WHERE m.session_id = ? ORDER BY m.rowid""",
            (sid,),
        )

    def get_upload(self, sid, user_id):
        r = self._one(
            "SELECT uploads FROM session_members WHERE session_id = ? AND user_id = ?",
            (sid, user_id),
        )
        return r["uploads"] if r else 0

    def inc_upload(self, sid, user_id):
        self._exec(
            "UPDATE session_members SET uploads = uploads + 1 WHERE session_id = ? AND user_id = ?",
            (sid, user_id),
        )

    def add_session_track(self, sid, user_id, file_id, title, performer, duration):
        self._exec(
            """INSERT INTO session_tracks (session_id, user_id, file_id, title, performer, duration)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sid, user_id, file_id, title or "", performer or "", duration or 0),
        )

    def member_track_at(self, sid, user_id, offset):
        return self._one(
            """SELECT * FROM session_tracks WHERE session_id = ? AND user_id = ?
               ORDER BY id LIMIT 1 OFFSET ?""",
            (sid, user_id, offset),
        )

    def set_track_slot(self, track_id, slot):
        self._exec("UPDATE session_tracks SET slot = ? WHERE id = ?", (slot, track_id))

    def session_tracks(self, sid):
        return self._all(
            "SELECT * FROM session_tracks WHERE session_id = ? ORDER BY slot, id",
            (sid,),
        )

    def delete_session(self, sid):
        self._exec("DELETE FROM session_tracks WHERE session_id = ?", (sid,))
        self._exec("DELETE FROM session_members WHERE session_id = ?", (sid,))
        self._exec("DELETE FROM playlist_likes WHERE playlist_id = ?", (sid,))
        self._exec("DELETE FROM sessions WHERE session_id = ?", (sid,))

    def close_user_private_sessions(self, user_id):
        """🧹 جلسات خصوصی نیمه‌کاره قدیمی را می‌بندد تا مانع جلسه جدید نشوند"""
        rows = self._all(
            """SELECT s.session_id AS sid FROM sessions s
               JOIN session_members m ON m.session_id = s.session_id
               WHERE m.user_id = ? AND s.kind = 'private' AND s.state = 'uploading'""",
            (user_id,),
        )
        for r in rows:
            self.set_session_fields(r["sid"], state="done")

    def get_user_upload_session(self, user_id, kind="private"):
        return self._one(
            """SELECT s.* FROM sessions s
               JOIN session_members m ON m.session_id = s.session_id
               WHERE m.user_id = ? AND s.kind = ? AND s.state = 'uploading'
               ORDER BY s.session_id DESC LIMIT 1""",
            (user_id, kind),
        )

    def get_group_session(self, chat_id):
        return self._one(
            """SELECT * FROM sessions WHERE chat_id = ? AND kind = 'group'
               AND state IN ('uploading', 'playing')
               ORDER BY session_id DESC LIMIT 1""",
            (chat_id,),
        )

    # ---------- لایک پلی‌لیست‌های محبوب ----------
    def like_playlist(self, sid, user_id) -> bool:
        cur = self._exec(
            "INSERT OR IGNORE INTO playlist_likes (playlist_id, user_id) VALUES (?, ?)",
            (sid, user_id),
        )
        return cur.rowcount > 0

    def unlike_playlist(self, sid, user_id):
        self._exec(
            "DELETE FROM playlist_likes WHERE playlist_id = ? AND user_id = ?",
            (sid, user_id),
        )

    def has_liked(self, sid, user_id) -> bool:
        return self._one(
            "SELECT 1 AS x FROM playlist_likes WHERE playlist_id = ? AND user_id = ?",
            (sid, user_id),
        ) is not None

    def like_count(self, sid) -> int:
        r = self._one("SELECT COUNT(*) AS c FROM playlist_likes WHERE playlist_id = ?", (sid,))
        return r["c"] if r else 0

    def popular_playlists(self, limit=15):
        """🔥 پلی‌لیست‌های عمومی، مرتب بر اساس تعداد لایک (بیشترین اول)"""
        return self._all(
            """SELECT s.session_id, s.title, s.genre, s.size, s.state,
                      COUNT(DISTINCT l.user_id) AS likes,
                      (SELECT COUNT(*) FROM session_tracks t
                        WHERE t.session_id = s.session_id) AS ntracks
               FROM sessions s
               LEFT JOIN playlist_likes l ON l.playlist_id = s.session_id
               WHERE s.public = 1 AND s.state IN ('playing', 'done')
               GROUP BY s.session_id
               ORDER BY likes DESC, s.session_id DESC
               LIMIT ?""",
            (limit,),
        )

    # ---------- پلی‌لیست شخصی ----------
    def add_personal_track(self, user_id, file_id, title, performer, duration):
        self._exec(
            """INSERT INTO personal_tracks (user_id, file_id, title, performer, duration)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, file_id, title or "", performer or "", duration or 0),
        )

    def personal_tracks(self, user_id):
        return self._all(
            "SELECT * FROM personal_tracks WHERE user_id = ? ORDER BY id",
            (user_id,),
        )

    def delete_personal_track(self, tid, user_id) -> bool:
        cur = self._exec(
            "DELETE FROM personal_tracks WHERE id = ? AND user_id = ?",
            (tid, user_id),
        )
        return cur.rowcount > 0

    # ---------- آمار ----------
    def stats(self):
        return {
            "users": self.count_users(),
            "sessions": self._one("SELECT COUNT(*) AS c FROM sessions")["c"],
            "tracks": self._one("SELECT COUNT(*) AS c FROM session_tracks")["c"],
            "buddies": self._one("SELECT COUNT(*) AS c FROM buddies")["c"],
            "likes": self._one("SELECT COUNT(*) AS c FROM playlist_likes")["c"],
        }

    def admin_stats(self):
        return {
            "users": self.count_users(),
            "pro": self._one("SELECT COUNT(*) AS c FROM users WHERE is_pro = 1")["c"],
            "banned": self._one("SELECT COUNT(*) AS c FROM users WHERE banned = 1")["c"],
            "sessions": self._one("SELECT COUNT(*) AS c FROM sessions")["c"],
            "tracks": self._one("SELECT COUNT(*) AS c FROM session_tracks")["c"],
            "buddies": self._one("SELECT COUNT(*) AS c FROM buddies")["c"],
            "likes": self._one("SELECT COUNT(*) AS c FROM playlist_likes")["c"],
            "referrals": self._one("SELECT COUNT(*) AS c FROM referrals")["c"],
        }