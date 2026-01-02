# antispam_core/cleaner.py
import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Dict

from pyrogram import Client, errors
from pyrogram.enums import ChatType

from .client.client_manager import get_or_start_client, get_active_accounts

# ============================================================
# ⚙️ سیستم لاگ با نانوثانیه (مثل ماژول اسپمر)
# ============================================================
class NanoFormatter(logging.Formatter):
    """Formatter برای نمایش زمان دقیق تا نانوثانیه."""
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        ns = int((record.created - int(record.created)) * 1_000_000_000)
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}.{ns:09d}"

logger = logging.getLogger("clean_acc")
logger.setLevel(logging.DEBUG)

os.makedirs("logs", exist_ok=True)
_log_path = "logs/clean_acc.txt"

if not any(
    isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "").endswith("clean_acc.txt")
    for h in logger.handlers
):
    fh = logging.FileHandler(_log_path, encoding="utf-8")
    fh.setFormatter(NanoFormatter("%(asctime)s - %(levelname)s - %(message)s"))
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

logger.info("🧹 cleaner logger initialized -> %s", _log_path)

# ============================================================
# 🧩 تابع کمکی
# ============================================================
def _chat_info(chat) -> str:
    return f"id={getattr(chat,'id',None)} type={getattr(chat,'type',None)} " \
           f"title={getattr(chat,'title',None)!r} username={getattr(chat,'username',None)!r}"

# ============================================================
# 🧹 پاکسازی اکانت
# ============================================================
async def wipe_account_dialogs(cli: Client) -> Dict[str, int]:
    stats = {"left": 0, "pv_deleted": 0, "bots_blocked": 0, "fails": 0}
    start_time = time.time()
    try:
        me = await cli.get_me()
        logger.info("🚀 شروع پاکسازی اکانت %s (%s)", me.id, me.username)
    except Exception as e:
        logger.warning("❌ دریافت اطلاعات اکانت ناموفق: %s", e, exc_info=True)

    try:
        async for dialog in cli.get_dialogs():
            chat = dialog.chat
            info = _chat_info(chat)
            ctype = chat.type
            logger.debug(f"🔍 بررسی چت: {info}")

            try:
                if ctype in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL):
                    logger.info("👋 خروج از گروه/کانال: %s", info)
                    try:
                        await cli.leave_chat(chat.id, delete=True)
                        stats["left"] += 1
                        logger.debug("✅ Left OK (%d)", stats["left"])
                    except errors.FloodWait as e:
                        logger.warning("⚠️ FloodWait(%ss) در leave_chat: %s", e.value, info)
                        await asyncio.sleep(e.value)
                        try:
                            await cli.delete_history(chat.id, revoke=True)
                        except Exception:
                            logger.debug("❌ fallback delete_history fail", exc_info=True)
                        stats["left"] += 1
                    except Exception as e:
                        logger.error("❌ leave_chat failed: %s | %s", info, e, exc_info=True)
                        stats["fails"] += 1
                    await asyncio.sleep(0.35)

                elif ctype == ChatType.PRIVATE:
                    is_bot = getattr(chat, "is_bot", False)
                    is_self = getattr(chat, "is_self", False)
                    if is_self:
                        logger.debug("⏭️ Skip self chat: %s", info)
                        continue

                    logger.info("🗑️ حذف پیام‌ها در PV: %s", info)
                    try:
                        await cli.delete_history(chat.id, revoke=True)
                        stats["pv_deleted"] += 1
                    except errors.FloodWait as e:
                        logger.warning("⚠️ FloodWait(%ss) در delete_history: %s", e.value, info)
                        await asyncio.sleep(e.value)
                        try:
                            await cli.delete_history(chat.id, revoke=True)
                            stats["pv_deleted"] += 1
                        except Exception:
                            stats["fails"] += 1
                            logger.debug("❌ delete_history retry fail", exc_info=True)
                    except Exception:
                        stats["fails"] += 1
                        logger.debug("❌ delete_history fail", exc_info=True)

                    if is_bot:
                        logger.info("🤖 بلاک کردن بات: %s", info)
                        try:
                            await cli.block_user(chat.id)
                            stats["bots_blocked"] += 1
                        except errors.FloodWait as e:
                            logger.warning("⚠️ FloodWait(%ss) در block_user: %s", e.value, info)
                            await asyncio.sleep(e.value)
                            try:
                                await cli.block_user(chat.id)
                                stats["bots_blocked"] += 1
                            except Exception:
                                stats["fails"] += 1
                                logger.debug("❌ block_user retry fail", exc_info=True)
                        except Exception:
                            stats["fails"] += 1
                            logger.debug("❌ block_user fail", exc_info=True)
                    await asyncio.sleep(0.25)

                else:
                    try:
                        await cli.delete_history(chat.id, revoke=True)
                    except Exception:
                        logger.debug("delete_history (other type) fail", exc_info=True)

            except errors.FloodWait as e:
                logger.warning("⏸️ FloodWait(%ss) کلی در %s", e.value, info)
                await asyncio.sleep(e.value)
            except Exception as e:
                stats["fails"] += 1
                logger.error("💥 wipe step failed: %s | %s", info, e, exc_info=True)

    except Exception as e:
        logger.error("💥 iterate dialogs failed: %s", e, exc_info=True)

    duration = time.time() - start_time
    logger.info("✅ پایان پاکسازی اکانت (%s): %s | زمان: %.2fs", getattr(cli, 'phone_number', 'N/A'), stats, duration)
    logger.info("-" * 70)
    return stats

# ============================================================
# 🧩 فرمان اصلی برای همه اکانت‌ها
# ============================================================
async def del_all_pv_gp_ch_en_cmd(message):
    logger.info("⚙️ اجرای del_all_pv_gp_ch_en_cmd شروع شد...")
    try:
        acc_list = get_active_accounts()
        if not acc_list:
            await message.reply("❌ هیچ اکانتی پیدا نشد.")
            logger.warning("🚫 هیچ اکانتی فعال نیست.")
            return

        total = len(acc_list)
        ok = 0
        report_lines = ["🧹 <b>شروع پاک‌سازی کامل همه گفتگوها...</b>"]

        for phone in acc_list:
            logger.info("📱 شروع پاکسازی برای: %s", phone)
            try:
                cli = await get_or_start_client(phone)
                if cli is None:
                    report_lines.append(f"• {phone}: ✖️ کلاینت در دسترس نیست")
                    logger.warning("%s: client unavailable", phone)
                    continue

                stats = await wipe_account_dialogs(cli)
                ok += 1
                report_lines.append(
                    f"• {phone}: ✅ Left: {stats['left']} | PV del: {stats['pv_deleted']} | "
                    f"Bots blocked: {stats['bots_blocked']} | Fails: {stats['fails']}"
                )

                await asyncio.sleep(0.8)

            except errors.FloodWait as e:
                logger.warning("%s: FloodWait(%ss)", phone, e.value)
                await asyncio.sleep(e.value)
                report_lines.append(f"• {phone}: ⚠️ FloodWait({e.value})")
            except Exception as ex:
                logger.error("%s: error: %s", phone, ex, exc_info=True)
                report_lines.append(f"• {phone}: ✖️ خطا: {ex}")

        summary = f"\n📊 نتیجه نهایی: ✅ موفق برای {ok}/{total} اکانت"
        report_lines.append(summary)
        logger.info("🎯 پاکسازی کامل تمام شد. موفق: %d / کل: %d", ok, total)
        await message.reply("\n".join(report_lines))

    except Exception as e:
        logger.error("💥 خطا در اجرای del_all_pv_gp_ch_en_cmd: %s", e, exc_info=True)
        await message.reply(f"خطا در اجرای delallpvgpchenl: {e}")
