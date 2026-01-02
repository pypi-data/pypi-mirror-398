import os
import sqlite3
import logging
import time
import shutil
from datetime import datetime

# ============================================================
# ⚙️ تنظیمات لاگ
# ============================================================
os.makedirs("logs", exist_ok=True)
LOG_FILE = "logs/sqlite_health.log"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "").endswith(LOG_FILE) for h in logger.handlers):
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

# ============================================================
# 📦 تنظیمات و ثابت‌ها
# ============================================================
SIDE_SUFFIXES = (".session-wal", ".session-shm", ".session-journal")
BACKUP_SUFFIX = ".bak"
MAX_DB_SIZE_MB = 100  # حداکثر اندازه مجاز فایل دیتابیس
PROBE_TIMEOUT = 2.0   # زمان انتظار probe

# ============================================================
# 📁 اطمینان از وجود مسیر
# ============================================================
def ensure_dir(path: str):
    """ساخت مسیر در صورت عدم وجود"""
    try:
        os.makedirs(path, exist_ok=True)
        os.chmod(path, 0o777)
        logger.debug("✅ Directory ensured: %s", path)
    except Exception as e:
        logger.error("❌ Cannot create directory %s: %s: %s", path, type(e).__name__, e)

# ============================================================
# 🧩 تغییر سطح دسترسی فایل‌ها
# ============================================================
def chmod_rw(path: str):
    """تنظیم سطح دسترسی read/write برای فایل"""
    try:
        os.chmod(path, 0o666)
        logger.debug("🟢 chmod applied: %s", path)
    except Exception:
        pass

# ============================================================
# 🧹 حذف فایل‌های جانبی SQLite
# ============================================================
def cleanup_sqlite_sidecars(db_without_ext: str):
    """
    پاک‌سازی فایل‌های جانبی مربوط به SQLite (.wal, .shm, .journal)
    """
    base = f"{db_without_ext}.session"
    for suf in ("-wal", "-shm", "-journal"):
        f = f"{base}{suf}"
        if os.path.exists(f):
            try:
                os.remove(f)
                logger.debug("🧽 Removed sqlite sidecar: %s", f)
            except Exception as e:
                logger.warning("⚠️ Cannot remove sidecar %s: %s", f, e)

# ============================================================
# 🔍 بررسی سلامت دیتابیس
# ============================================================
def probe_sqlite(db_file: str) -> bool:
    """
    بررسی سلامت دیتابیس SQLite (قابل باز شدن بودن)
    """
    if not os.path.exists(db_file):
        logger.warning("⚠️ probe_sqlite: file not found: %s", db_file)
        return False

    try:
        start = time.time()
        conn = sqlite3.connect(db_file, timeout=PROBE_TIMEOUT)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA integrity_check;")
        conn.close()
        elapsed = (time.time() - start) * 1000
        logger.info("✅ SQLite probe OK for %s (%.1f ms)", db_file, elapsed)
        return True
    except sqlite3.DatabaseError as e:
        logger.error("❌ SQLite probe failed (%s): %s", db_file, e)
        return False
    except Exception as e:
        logger.error("💥 SQLite probe critical error (%s): %s: %s", db_file, type(e).__name__, e)
        return False

# ============================================================
# 🧰 ابزارهای کمکی برای دیتابیس
# ============================================================
def get_db_stats(db_file: str) -> dict:
    """اطلاعات متا درباره دیتابیس برمی‌گرداند"""
    try:
        if not os.path.exists(db_file):
            return {"exists": False}

        stat = os.stat(db_file)
        return {
            "exists": True,
            "size_mb": round(stat.st_size / (1024 * 1024), 3),
            "last_modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "permissions": oct(stat.st_mode)[-3:]
        }
    except Exception as e:
        logger.error("⚠️ Error getting DB stats for %s: %s", db_file, e)
        return {"exists": False, "error": str(e)}

# ============================================================
# 💾 پشتیبان‌گیری از دیتابیس
# ============================================================
def backup_sqlite(db_file: str) -> str:
    """ایجاد نسخه پشتیبان از دیتابیس"""
    if not os.path.exists(db_file):
        logger.warning("⚠️ Cannot backup, file not found: %s", db_file)
        return ""

    backup_path = f"{db_file}{BACKUP_SUFFIX}"
    try:
        shutil.copy2(db_file, backup_path)
        logger.info("🧩 Backup created: %s", backup_path)
        return backup_path
    except Exception as e:
        logger.error("❌ Error creating backup for %s: %s", db_file, e)
        return ""

# ============================================================
# 🔧 تعمیر خودکار دیتابیس
# ============================================================
def repair_sqlite(db_file: str) -> bool:
    """
    تلاش برای تعمیر دیتابیس خراب.
    - ایجاد بک‌آپ
    - حذف sidecarها
    - اجرای vacuum برای بازسازی
    """
    if not os.path.exists(db_file):
        logger.warning("⚠️ repair_sqlite: file not found: %s", db_file)
        return False

    backup_sqlite(db_file)
    cleanup_sqlite_sidecars(db_file.replace(".session", ""))

    try:
        conn = sqlite3.connect(db_file, timeout=5)
        conn.execute("PRAGMA integrity_check;")
        conn.execute("VACUUM;")
        conn.execute("PRAGMA optimize;")
        conn.close()
        logger.info("🧠 SQLite repaired successfully: %s", db_file)
        return True
    except Exception as e:
        logger.error("❌ SQLite repair failed for %s: %s", db_file, e)
        return False

# ============================================================
# 🩺 بررسی کلی سلامت دیتابیس
# ============================================================
def validate_session_db(db_file: str) -> bool:
    """
    بررسی سلامت کامل یک فایل session:
    - وجود فایل
    - سایز منطقی
    - probe موفق
    - پاک‌سازی در صورت نیاز
    """
    stats = get_db_stats(db_file)
    if not stats.get("exists"):
        logger.warning("⚠️ DB does not exist: %s", db_file)
        return False

    if stats.get("size_mb", 0) > MAX_DB_SIZE_MB:
        logger.warning("⚠️ DB too large (%s MB): %s", stats["size_mb"], db_file)
        return False

    ok = probe_sqlite(db_file)
    if not ok:
        logger.warning("⚠️ SQLite probe failed, attempting repair...")
        repaired = repair_sqlite(db_file)
        return repaired

    logger.info("✅ DB %s validated OK", db_file)
    return True

# ============================================================
# 🧹 حذف دیتابیس و فایل‌های مرتبط
# ============================================================
def remove_sqlite_full(db_without_ext: str):
    """حذف دیتابیس اصلی و تمام sidecarها"""
    db = f"{db_without_ext}.session"
    try:
        if os.path.exists(db):
            os.remove(db)
            logger.info("🗑 Removed DB: %s", db)
    except Exception as e:
        logger.warning("⚠️ Cannot remove DB %s: %s", db, e)
    cleanup_sqlite_sidecars(db_without_ext)

# ============================================================
# 🔍 تست سریع در محیط توسعه
# ============================================================
if __name__ == "__main__":
    test_db = "acc/test_account.session"
    print("🔍 Probing:", test_db)
    ok = probe_sqlite(test_db)
    print("Probe result:", ok)
    print("Stats:", get_db_stats(test_db))
