# remote/joiner.py
import asyncio
import os
import logging
import re
from pyrogram import errors
from ..core.precise_engine import PreciseTicker

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ساخت فولدر لاگ و هندلر مخصوص این ماژول
os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler("logs/join_log.txt", encoding="utf-8")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
# جلوگیری از اضافه‌شدن هندلر تکراری
if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "").endswith("join_log.txt")
           for h in logger.handlers):
    logger.addHandler(file_handler)


def _normalize_target(raw: str):
    """
    ورودی را نرمالایز می‌کند و یکی از حالت‌ها را برمی‌گرداند:
      ('invite', invite_hash, original_has_joinchat: bool)
      ('username', username, None)
      ('chat_id', int_chat_id, None)
    """
    if raw is None:
        return None, None, None

    s = str(raw).strip()

    # برای تشخیص اینکه ورودی joinchat بوده یا +hash
    original_has_joinchat = "joinchat" in s.lower()

    # پاکسازی پروتکل و www
    s = re.sub(r'^(?:https?://)', '', s, flags=re.I)
    s = re.sub(r'^www\.', '', s, flags=re.I)

    # اگر شامل slash است، آخرین بخش مسیر را بگیر
    if '/' in s:
        s = s.split('/')[-1]

    # هندل ورودی‌های اشتباه مثل Unity_Darkness.T.me
    m = re.search(r'^(?P<name>.*?)\.(?:t\.me|telegram\.me)$', s, flags=re.I)
    if m:
        s = m.group("name")

    # حذف query و کاراکترهای نامطلوب
    s = s.split('?')[0].strip()
    s = s.strip('<> "\'')

    # حذف @ از ابتدای یوزرنیم
    if s.startswith('@'):
        s = s[1:].strip()

    # شروع با + یعنی invite hash
    if s.startswith('+'):
        return 'invite', s.lstrip('+').strip(), False

    # chat_id عددی
    if s.lstrip('-').isdigit():
        try:
            return 'chat_id', int(s), None
        except Exception:
            pass

    # اگر طول و کاراکترها مناسب بود
    if re.match(r'^[A-Za-z0-9_\-]{8,}$', s):
        # طول >= 20 را invite فرض کن (غالباً هش دعوت)
        if len(s) >= 20:
            return 'invite', s, original_has_joinchat
        # در غیر این صورت یوزرنیم
        return 'username', s, None

    # fallback: یوزرنیم
    return 'username', s, None


async def join_all(acc_list, link, get_or_start_client):
    """
    تمام اکانت‌ها را به لینک مشخص‌شده جوین می‌کند.
    از یوزرنیم، chat_id و لینک‌های دعوت (+hash / joinchat/hash) پشتیبانی می‌شود.
    """
    ticker = PreciseTicker(1.0)
    success, failed = 0, 0

    logger.info(f"🚀 شروع عملیات Join برای لینک: {link}")
    logger.info(f"📱 تعداد اکانت‌ها: {len(acc_list)}")

    ttype, tval, aux = _normalize_target(link)
    if ttype is None:
        logger.error("ورودی لینک خالی یا نامعتبر است.")
        return 0, len(acc_list)

    for phone in acc_list:
        try:
            cli = await get_or_start_client(phone)
            if not cli:
                logger.warning(f"{phone}: ❌ Client could not be started.")
                failed += 1
                await ticker.sleep()
                continue

            if ttype == 'invite':
                # بازسازی لینک کامل برای Pyrogram
                invite_hash = str(tval).lstrip('+').strip()
                if aux is True:
                    # اگر ورودی از نوع joinchat تشخیص داده شد، همان فرمت را بساز
                    invite_link = f"https://t.me/joinchat/{invite_hash}"
                else:
                    # در غیر این صورت فرمت جدید +hash
                    invite_link = f"https://t.me/+{invite_hash}"

                try:
                    # در Pyrogram جدید: join_chat با لینک دعوت
                    await cli.join_chat(invite_link)
                    logger.info(f"{phone}: ✅ Joined via invite link {invite_link}")
                    success += 1

                except errors.UserAlreadyParticipant:
                    logger.info(f"{phone}: ⚙️ Already in chat (invite).")
                    success += 1

                except errors.FloodWait as e:
                    logger.warning(f"{phone}: ⏰ FloodWait {e.value}s")
                    await asyncio.sleep(e.value)
                    failed += 1

                except errors.BadRequest as e:
                    # شامل مواردی مثل InviteHashInvalid/Expired ولی به صورت کلی
                    logger.warning(f"{phone}: ⚠️ BadRequest on invite ({invite_link}): {e}")
                    failed += 1

                except Exception as e:
                    logger.warning(f"{phone}: ❌ Failed to join by invite: {type(e).__name__} - {e}")
                    failed += 1

            elif ttype == 'chat_id':
                chat_id = tval
                try:
                    await cli.join_chat(chat_id)
                    logger.info(f"{phone}: ✅ Joined chat_id {chat_id}")
                    success += 1
                except errors.UserAlreadyParticipant:
                    logger.info(f"{phone}: ⚙️ Already in chat_id {chat_id}")
                    success += 1
                except errors.FloodWait as e:
                    logger.warning(f"{phone}: ⏰ FloodWait {e.value}s")
                    await asyncio.sleep(e.value)
                    failed += 1
                except Exception as e:
                    logger.warning(f"{phone}: ❌ Failed to join chat_id {chat_id}: {type(e).__name__} - {e}")
                    failed += 1

            else:  # username
                username = str(tval).lstrip('@').strip()
                try:
                    await cli.join_chat(username)
                    logger.info(f"{phone}: ✅ Joined public chat @{username}")
                    success += 1

                except errors.UserAlreadyParticipant:
                    logger.info(f"{phone}: ⚙️ Already in public chat @{username}")
                    success += 1

                except errors.UsernameInvalid:
                    logger.warning(f"{phone}: ⚠️ Invalid username @{username}")
                    failed += 1

                except errors.ChannelPrivate:
                    logger.warning(f"{phone}: 🔒 Cannot access @{username} (private/restricted)")
                    failed += 1

                except errors.FloodWait as e:
                    logger.warning(f"{phone}: ⏰ FloodWait {e.value}s")
                    await asyncio.sleep(e.value)
                    failed += 1

                except Exception as e:
                    logger.warning(f"{phone}: ❌ Failed to join public chat @{username}: {type(e).__name__} - {e}")
                    failed += 1

        except Exception as e:
            logger.error(f"{phone}: 💥 Fatal join error {type(e).__name__} - {e}")
            failed += 1

        await ticker.sleep()

    logger.info(f"🎯 Join completed → Success: {success} | Failed: {failed}")
    logger.info("------------------------------------------------------\n")

    return success, failed
