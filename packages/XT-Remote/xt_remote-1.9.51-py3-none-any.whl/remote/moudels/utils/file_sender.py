# antispam_core/file_sender.py
import os, asyncio, logging
from typing import Optional, List
from pyrogram import errors
from ..core.config import ACCOUNTS_FOLDER, ACCOUNTS_DATA_FOLDER

logger = logging.getLogger(__name__)

# =====================================================
# 📤 ارسال امن فایل به چت (با مدیریت FloodWait)
# =====================================================

async def _safe_send_document(app, chat_id: int, path: str, caption: Optional[str] = None, max_retries: int = 2) -> bool:
    """
    ارسال امن فایل با چند تلاش مجدد در صورت خطا یا FloodWait
    """
    for attempt in range(max_retries):
        try:
            await app.send_document(chat_id, path, caption=caption or os.path.basename(path))
            return True
        except errors.FloodWait as e:
            logger.warning(f"FloodWait ({e.value}s) هنگام ارسال {path}")
            await asyncio.sleep(e.value)
        except Exception as e:
            logger.warning(f"تلاش {attempt+1} برای ارسال {path} با خطا مواجه شد: {e}")
            await asyncio.sleep(1.2)
    return False


# =====================================================
# 📂 ارسال تمام فایل‌های پوشه (با فیلتر پسوند)
# =====================================================

async def _send_all_from_folder(app, message, folder: str, allowed_exts: Optional[List[str]] = None):
    """
    ارسال همه فایل‌های موجود در یک پوشه (فقط با پسوندهای مشخص)
    """
    try:
        if not os.path.isdir(folder):
            await message.reply(f"📁 پوشه وجود ندارد: {folder}")
            return

        files = []
        for fn in os.listdir(folder):
            full = os.path.join(folder, fn)
            if not os.path.isfile(full):
                continue
            if allowed_exts and not any(fn.lower().endswith(ext) for ext in allowed_exts):
                continue
            files.append(full)

        if not files:
            await message.reply("هیچ فایلی مطابق فیلتر پیدا نشد.")
            return

        files.sort(key=lambda p: os.path.basename(p).lower())

        await message.reply(f"📤 شروع ارسال {len(files)} فایل از {folder} ...")
        sent, failed = 0, 0

        for path in files:
            ok = await _safe_send_document(app, message.chat.id, path, caption=os.path.basename(path))
            if ok:
                sent += 1
            else:
                failed += 1
            await asyncio.sleep(0.35)

        await message.reply(f"✅ ارسال تمام شد.\nموفق: {sent} | ناموفق: {failed} | مجموع: {len(files)}")

    except Exception as e:
        logger.error(f"خطا در ارسال فایل‌ها از {folder}: {e}")
        await message.reply(f"❌ خطا در ارسال فایل‌ها: {e}")


# =====================================================
# ⚙️ دستورات مربوط به ارسال سشن‌ها
# =====================================================

async def give_sessions_cmd(app, message):
    """ارسال تمام فایل‌های .session از پوشه acc"""
    await _send_all_from_folder(app, message, ACCOUNTS_FOLDER, allowed_exts=[".session"])


async def give_data_sessions_cmd(app, message):
    """ارسال تمام فایل‌های .json از پوشه acc_data"""
    await _send_all_from_folder(app, message, ACCOUNTS_DATA_FOLDER, allowed_exts=[".json"])
