# antispam_core/block_manager.py
import asyncio, logging
from typing import Optional, Union
from pyrogram import errors
from ..account.client.client_manager import get_or_start_client, accounts

logger = logging.getLogger(__name__)

# ===============================
# 🔍 استخراج هدف از پیام (user)
# ===============================
def _extract_target_user_from_message(message) -> Optional[Union[int, str]]:
    """
    برمی‌گرداند: int user_id یا str username
    از یکی از حالت‌ها می‌خواند:
    ریپلای، tg://user?id=..., @username, t.me/username، یا عدد خام.
    """
    try:
        if message.reply_to_message and message.reply_to_message.from_user:
            return int(message.reply_to_message.from_user.id)
    except Exception:
        pass

    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            return None
        s = parts[1].strip()
        if not s:
            return None

        s_low = s.lower()

        if s_low.startswith("tg://user?id="):
            v = s.split("=", 1)[1].strip()
            return int(v)

        if "t.me/" in s_low:
            v = s.split("/")[-1]
            v = v.split("?")[0].strip()
            if v.startswith("@"):
                v = v[1:]
            if v.isdigit():
                return int(v)
            return v

        if s.startswith("@"):
            return s[1:]

        if s.lstrip("+-").isdigit():
            return int(s)

        return s
    except Exception:
        return None


# ===============================
# 🚫 بلاک کاربر در تمام اکانت‌ها
# ===============================
async def block_user_all_cmd(message):
    target = _extract_target_user_from_message(message)
    if target is None:
        await message.reply("استفاده: `block USERID_OR_USERNAME`\nیا به پیام کاربر ریپلای کن و بزن `block`")
        return

    acc_list = accounts()
    if not acc_list:
        await message.reply("❌ هیچ اکانتی پیدا نشد.")
        return

    ok, fail = 0, 0
    lines = [f"🚫 شروع بلاک کاربر: {target}"]

    for phone in acc_list:
        try:
            cli = await get_or_start_client(phone)
            if cli is None:
                lines.append(f"• {phone}: کلاینت در دسترس نیست")
                fail += 1
                continue

            try:
                await cli.block_user(target)
                ok += 1
                lines.append(f"• {phone}: ✅ بلاک شد")
            except errors.FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await cli.block_user(target)
                    ok += 1
                    lines.append(f"• {phone}: ✅ بلاک شد (بعد از FloodWait)")
                except Exception as ex2:
                    fail += 1
                    lines.append(f"• {phone}: ✖️ خطا بعد از FloodWait: {ex2}")
            except Exception as ex:
                fail += 1
                lines.append(f"• {phone}: ✖️ {ex}")

            await asyncio.sleep(0.25)

        except Exception as e:
            fail += 1
            lines.append(f"• {phone}: ✖️ خطا: {e}")

    lines.append(f"\nنتیجه: ✅ موفق {ok} / ❌ ناموفق {fail} / مجموع {len(acc_list)}")
    out = "\n".join(lines)
    if len(out) > 3900:
        out = out[:3800] + "\n... (trimmed)"
    await message.reply(out)


# ===============================
# ✅ آنبلاک کاربر در تمام اکانت‌ها
# ===============================
async def unblock_user_all_cmd(message):
    target = _extract_target_user_from_message(message)
    if target is None:
        await message.reply("استفاده: `unblock USERID_OR_USERNAME`\nیا به پیام کاربر ریپلای کن و بزن `unblock`")
        return

    acc_list = accounts()
    if not acc_list:
        await message.reply("❌ هیچ اکانتی پیدا نشد.")
        return

    ok, fail = 0, 0
    lines = [f"✅ شروع آنبلاک کاربر: {target}"]

    for phone in acc_list:
        try:
            cli = await get_or_start_client(phone)
            if cli is None:
                lines.append(f"• {phone}: کلاینت در دسترس نیست")
                fail += 1
                continue

            try:
                await cli.unblock_user(target)
                ok += 1
                lines.append(f"• {phone}: ✅ آنبلاک شد")
            except errors.FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await cli.unblock_user(target)
                    ok += 1
                    lines.append(f"• {phone}: ✅ آنبلاک شد (بعد از FloodWait)")
                except Exception as ex2:
                    fail += 1
                    lines.append(f"• {phone}: ✖️ خطا بعد از FloodWait: {ex2}")
            except Exception as ex:
                fail += 1
                lines.append(f"• {phone}: ✖️ {ex}")

            await asyncio.sleep(0.25)

        except Exception as e:
            fail += 1
            lines.append(f"• {phone}: ✖️ خطا: {e}")

    lines.append(f"\nنتیجه: ✅ موفق {ok} / ❌ ناموفق {fail} / مجموع {len(acc_list)}")
    out = "\n".join(lines)
    if len(out) > 3900:
        out = out[:3800] + "\n... (trimmed)"
    await message.reply(out)
