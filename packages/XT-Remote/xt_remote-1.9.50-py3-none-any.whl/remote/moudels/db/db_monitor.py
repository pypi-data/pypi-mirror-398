import os
import asyncio
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pyrogram import errors

from ..account.client.client_manager import ACCOUNTS_FOLDER
from ..db.sqlite_utils import (
    get_db_stats,
    probe_sqlite,
    repair_sqlite,
    validate_session_db,
    cleanup_sqlite_sidecars,
)

# ============================================================
# ⚙️ تنظیمات لاگ
# ============================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================
# 📦 تنظیمات کلی
# ============================================================
MAX_WORKERS = 6  # تعداد رشته‌ها برای بررسی موازی
PROGRESS_SYMBOLS = ["⣷", "⣯", "⣟", "⡿", "⢿", "⣻", "⣽", "⣾"]

# ============================================================
# 📁 ابزار کمکی
# ============================================================
def list_sessions() -> list:
    """لیست تمام فایل‌های سشن موجود"""
    if not os.path.isdir(ACCOUNTS_FOLDER):
        return []
    return sorted(
        [os.path.splitext(f)[0] for f in os.listdir(ACCOUNTS_FOLDER) if f.endswith(".session")]
    )


def format_status_row(name: str, stats: dict, state: str) -> str:
    """فرمت‌بندی نمایشی هر سشن"""
    emoji = {
        "healthy": "🟢",
        "warning": "🟡",
        "corrupt": "🔴",
        "missing": "⚫️",
    }.get(state, "❔")

    size = stats.get("size_mb", "?")
    modified = stats.get("last_modified", "?")
    return f"{emoji} `{name}` | {size}MB | {modified}"


async def _progress_bar(total: int, current: int, start_time: float) -> str:
    """ساخت نوار پیشرفت متنی"""
    percent = (current / total) * 100 if total else 0
    elapsed = time.time() - start_time
    spinner = PROGRESS_SYMBOLS[int(current) % len(PROGRESS_SYMBOLS)]
    return f"{spinner} {current}/{total} ({percent:.1f}%) ⏱ {elapsed:.1f}s"


# ============================================================
# 🩺 بررسی سلامت دیتابیس‌ها
# ============================================================
async def db_status_cmd(message):
    """
    بررسی سلامت دیتابیس‌ها با نوار پیشرفت و گزارش کامل
    """
    try:
        sessions = list_sessions()
        if not sessions:
            await message.reply("⚠️ هیچ سشنی یافت نشد.")
            return

        reply_msg = await message.reply("🔍 در حال بررسی سلامت دیتابیس‌ها... لطفاً صبر کنید")

        loop = asyncio.get_event_loop()
        start = time.time()
        healthy, warnings, broken, missing = [], [], [], []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            tasks = []
            for sess in sessions:
                db_path = os.path.join(ACCOUNTS_FOLDER, f"{sess}.session")

                def check_status():
                    if not os.path.exists(db_path):
                        return (sess, "missing", {})
                    stats = get_db_stats(db_path)
                    if not stats.get("exists"):
                        return (sess, "missing", stats)
                    if probe_sqlite(db_path):
                        return (sess, "healthy", stats)
                    else:
                        return (sess, "warning", stats)

                tasks.append(loop.run_in_executor(executor, check_status))

            total = len(tasks)
            for i, fut in enumerate(asyncio.as_completed(tasks), 1):
                sess, state, stats = await fut
                if state == "healthy":
                    healthy.append(format_status_row(sess, stats, "healthy"))
                elif state == "warning":
                    warnings.append(format_status_row(sess, stats, "warning"))
                elif state == "missing":
                    missing.append(format_status_row(sess, stats, "missing"))
                else:
                    broken.append(format_status_row(sess, stats, "corrupt"))

                bar = await _progress_bar(total, i, start)
                await reply_msg.edit_text(f"🔍 بررسی در حال انجام...\n{bar}")

        total_time = time.time() - start
        report = [
            f"📊 **گزارش وضعیت دیتابیس‌ها**",
            f"🕒 زمان بررسی: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
            f"⏱ مدت زمان: {total_time:.2f}s",
            "",
        ]

        if healthy:
            report.append(f"✅ سالم ({len(healthy)}):")
            report.extend(healthy)
            report.append("")
        if warnings:
            report.append(f"⚠️ نیاز به بررسی ({len(warnings)}):")
            report.extend(warnings)
            report.append("")
        if missing:
            report.append(f"❌ از بین رفته ({len(missing)}):")
            report.extend(missing)
            report.append("")

        await reply_msg.edit_text("\n".join(report))
        logger.info("DB Status Report generated. Total: %d", len(sessions))

    except Exception as e:
        logger.exception("db_status_cmd error: %s", e)
        await message.reply(f"💥 خطا در بررسی دیتابیس‌ها: {e}")


# ============================================================
# 🔧 تعمیر دیتابیس‌ها
# ============================================================
async def db_repair_cmd(message):
    """
    تعمیر تمام دیتابیس‌های خراب با نمایش نوار پیشرفت و نتیجه
    """
    try:
        sessions = list_sessions()
        if not sessions:
            await message.reply("⚠️ هیچ دیتابیسی برای تعمیر وجود ندارد.")
            return

        reply_msg = await message.reply("🔧 شروع فرآیند تعمیر دیتابیس‌ها...")
        loop = asyncio.get_event_loop()
        start = time.time()

        repaired, failed = [], []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            tasks = []
            for sess in sessions:
                db_path = os.path.join(ACCOUNTS_FOLDER, f"{sess}.session")

                def repair_job():
                    if not os.path.exists(db_path):
                        return (sess, False)
                    result = validate_session_db(db_path)
                    return (sess, result)

                tasks.append(loop.run_in_executor(executor, repair_job))

            total = len(tasks)
            for i, fut in enumerate(asyncio.as_completed(tasks), 1):
                sess, ok = await fut
                if ok:
                    repaired.append(sess)
                else:
                    failed.append(sess)

                bar = await _progress_bar(total, i, start)
                await reply_msg.edit_text(f"🔧 تعمیر در حال انجام...\n{bar}")

        elapsed = time.time() - start
        summary = [
            "🧩 **گزارش تعمیر دیتابیس‌ها**",
            f"🕒 زمان اتمام: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
            f"⏱ مدت: {elapsed:.2f}s",
            "",
            f"✅ تعمیر موفق ({len(repaired)}): {', '.join(repaired) if repaired else '-'}",
            f"❌ تعمیر ناموفق ({len(failed)}): {', '.join(failed) if failed else '-'}",
        ]

        await reply_msg.edit_text("\n".join(summary))
        logger.info("DB Repair completed. OK=%d | FAIL=%d", len(repaired), len(failed))

    except Exception as e:
        logger.exception("db_repair_cmd error: %s", e)
        await message.reply(f"💥 خطا در تعمیر دیتابیس‌ها: {e}")
