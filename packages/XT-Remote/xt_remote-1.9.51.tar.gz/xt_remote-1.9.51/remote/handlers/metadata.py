"""
Command metadata for CliRemote bot.

این فایل فقط اطلاعات ثابتِ مربوط به کامندها رو نگه می‌داره
(مثلاً سطح دسترسی). منطق هندل کردن پیام‌ها جای دیگه پیاده می‌شه.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping


AccessLevel = Literal["admin", "owner"]


@dataclass(frozen=True)
class CommandMeta:
    name: str          # اسم کامند (بدون /)
    access: AccessLevel  # سطح دسترسی لازم برای اجرا
    needs_app: bool = False  # اگر True باشه، هندلر برای اجرا به app/client نیاز داره


# دیکشنری اصلی: اسم کامند -> متادیتا
COMMANDS: Mapping[str, CommandMeta] = {
    "add": CommandMeta(name="add", access="admin", needs_app=False),
    "code": CommandMeta(name="code", access="admin", needs_app=False),
    "pass": CommandMeta(name="pass", access="admin", needs_app=False),
    "del": CommandMeta(name="del", access="admin", needs_app=False),
    "delall": CommandMeta(name="delall", access="admin", needs_app=False),
    "listacc": CommandMeta(name="listacc", access="admin", needs_app=False),

    "givedatasessions": CommandMeta(name="givedatasessions", access="owner", needs_app=True),
    "delallpvgpchenl": CommandMeta(name="delallpvgpchenl", access="owner", needs_app=False),
    "givesessions": CommandMeta(name="givesessions", access="owner", needs_app=True),

    "text": CommandMeta(name="text", access="admin", needs_app=False),
    "ctext": CommandMeta(name="ctext", access="admin", needs_app=False),
    "shtext": CommandMeta(name="shtext", access="admin", needs_app=False),
    "shcap": CommandMeta(name="shcap", access="admin", needs_app=False),
    "cap": CommandMeta(name="cap", access="admin", needs_app=False),
    "ccap": CommandMeta(name="ccap", access="admin", needs_app=False),

    "textmention": CommandMeta(name="textmention", access="admin", needs_app=False),
    "mention_user": CommandMeta(name="mention_user", access="admin", needs_app=False),
    "mention_toggle": CommandMeta(name="mention_toggle", access="admin", needs_app=False),
    "mention_group_toggle": CommandMeta(name="mention_group_toggle", access="admin", needs_app=False),
    "mention_gps": CommandMeta(name="mention_gps", access="admin", needs_app=False),
    "mention_del": CommandMeta(name="mention_del", access="admin", needs_app=False),
    "mention_clear": CommandMeta(name="mention_clear", access="admin", needs_app=False),
    "mention_status": CommandMeta(name="mention_status", access="admin", needs_app=False),

    "gcode": CommandMeta(name="gcode", access="admin", needs_app=False),
    "restart": CommandMeta(name="restart", access="admin", needs_app=False),

    "join": CommandMeta(name="join", access="admin", needs_app=False),
    "leave": CommandMeta(name="leave", access="admin", needs_app=False),

    "addadmin": CommandMeta(name="addadmin", access="owner", needs_app=False),
    "deladmin": CommandMeta(name="deladmin", access="owner", needs_app=False),
    "admins": CommandMeta(name="admins", access="owner", needs_app=False),

    "profilesettings": CommandMeta(name="profilesettings", access="admin", needs_app=False),
    "setPic": CommandMeta(name="setPic", access="admin", needs_app=True),
    "delallprofile": CommandMeta(name="delallprofile", access="admin", needs_app=False),
    "name": CommandMeta(name="name", access="admin", needs_app=False),
    "bio": CommandMeta(name="bio", access="admin", needs_app=False),
    "username": CommandMeta(name="username", access="admin", needs_app=False),
    "remusername": CommandMeta(name="remusername", access="admin", needs_app=False),

    "block": CommandMeta(name="block", access="admin", needs_app=False),
    "unblock": CommandMeta(name="unblock", access="admin", needs_app=False),

    "dbstatus": CommandMeta(name="dbstatus", access="owner", needs_app=False),
    "dbrepair": CommandMeta(name="dbrepair", access="owner", needs_app=False),

    "spam": CommandMeta(name="spam", access="admin", needs_app=False),
    "stop": CommandMeta(name="stop", access="admin", needs_app=False),
    "speed": CommandMeta(name="speed", access="admin", needs_app=False),
    "set": CommandMeta(name="set", access="admin", needs_app=False),
    "stats": CommandMeta(name="stats", access="admin", needs_app=False),
}

OWNER_COMMANDS = {name for name, meta in COMMANDS.items() if meta.access == "owner"}
ADMIN_COMMANDS = {name for name, meta in COMMANDS.items() if meta.access == "admin"}
