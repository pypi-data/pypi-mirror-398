import os
import json
import asyncio
import logging
import random
import traceback
from typing import Optional, Dict, List, Set, Tuple
from pyrogram import Client, errors

# ============================================================
# ⚙️ تنظیم لاگ دقیق برای دیباگ Pyrogram و SQLite
# ============================================================
os.makedirs("logs", exist_ok=True)
log_file = "logs/client_debug_log.txt"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "").endswith(log_file) for h in logger.handlers):
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

logger.info("🧩 Client Manager loaded (v2.6, Full Persistent Device/App Version Support).")

# ============================================================
# 📁 مسیرها و ساختار داده‌ها
# ============================================================
BASE_DIR = os.path.abspath(os.getcwd())
ACCOUNTS_FOLDER = os.path.join(BASE_DIR, "acc")
ACCOUNTS_DATA_FOLDER = os.path.join(BASE_DIR, "acc_data")
ACC_TEMP = os.path.join(BASE_DIR, "acc_temp")

for p in (ACCOUNTS_FOLDER, ACCOUNTS_DATA_FOLDER, ACC_TEMP):
    os.makedirs(p, exist_ok=True)

client_pool: Dict[str, Client] = {}
client_locks: Dict[str, asyncio.Lock] = {}

# ============================================================
# 📱 لیست دستگاه‌ها و سیستم‌ها و نسخه‌های اپ (Device/System/App Version)
# (نسخه‌های app_version واقعی از تلگرام/تلگرام ایکس/فورک‌ها)
# ============================================================

DEVICE_NAME: List[str] = [
    "Samsung Galaxy S8", "Huawei P Smart 2021", "Xiaomi Redmi Note 9", "Samsung Galaxy A32",
    "OnePlus 7T Pro", "Google Pixel 6a", "Sony Xperia 10 IV", "Oppo Reno 8", "Vivo Y33s",
    "Realme 9 Pro+", "Asus Zenfone 8", "Nokia X30", "Honor 90", "Infinix Zero 20", "Tecno Camon 20 Pro"
]

# نیازی به هم‌اندازه بودن با DEVICE_NAME نیست؛ تصادفی انتخاب می‌شود
DEVICE_SYSTEM: List[str] = [
    "Android T10/0/1", "Android P11.1.1", "Android 12.0", "Android 13.0", "Android 12.1",
    "Android 13.1", "Android 14.0"
]

# نسخه‌های شناخته‌شده (رسمی و غیررسمی) برای app_version
DEVICE_APP_VERSIONS: List[str] = [
    "Telegram Android 12.1.1 (62112)",
    "Telegram Android 12.0.1",
    "Telegram Android 11.14.1",
    "Telegram Android 11.12.0",
    "Telegram Android 10.11.2",
    "Telegram X 0.27.10.1752",
    "Telegram X 0.26.8.1722-arm64-v8a",
    "Telegram X 0.28.0.1762 beta",
    "Plus Messenger 9.7.4",
    "Telegram+ 5.11.0"
]

def choose_device_pair() -> Tuple[str, str, str]:
    """
    یک سه‌تایی (device_model, system_version, app_version) تصادفی واقعی برمی‌گرداند.
    """
    device_model = random.choice(DEVICE_NAME)
    system_version = random.choice(DEVICE_SYSTEM)
    app_version = random.choice(DEVICE_APP_VERSIONS)
    return device_model, system_version, app_version

# ============================================================
# 🧱 ابزارهای فایل JSON
# ============================================================
def get_account_data(phone_number: str) -> Optional[Dict]:
    fp = os.path.join(ACCOUNTS_DATA_FOLDER, f"{phone_number}.json")
    if not os.path.exists(fp):
        logger.warning("%s: ⚠️ Account JSON not found → %s", phone_number, fp)
        return None
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("%s: ⚠️ Error reading JSON - %s: %s", phone_number, type(e).__name__, e)
        return None

def save_account_data(phone_number: str, data: Dict) -> None:
    fp = os.path.join(ACCOUNTS_DATA_FOLDER, f"{phone_number}.json")
    try:
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info("%s: 💾 Account JSON saved successfully.", phone_number)
    except Exception as e:
        logger.error("%s: ⚠️ Error saving JSON - %s: %s", phone_number, type(e).__name__, e)

# ============================================================
# 📲 مدیریت Device/System/AppVersion ثابت برای هر اکانت
# ============================================================
def get_or_assign_device_for_account(phone_number: str) -> Tuple[str, str, str]:
    """
    اگر در JSON مقادیر device_model/system_version/app_version موجود بود همان‌ها را برمی‌گرداند،
    در غیر این صورت مقدار تصادفی واقعی ایجاد و ذخیره می‌کند.
    """
    data = get_account_data(phone_number) or {}
    device_model = data.get("device_model")
    system_version = data.get("system_version")
    app_version = data.get("app_version")

    if device_model and system_version and app_version:
        logger.debug("%s: existing device found (%s | %s | %s)", phone_number, device_model, system_version, app_version)
        return device_model, system_version, app_version

    # اگر قبلی ناقص بود یا اصلاً نبود، یک سه‌تایی جدید بساز و ذخیره کن
    device_model, system_version, app_version = choose_device_pair()
    data["device_model"] = device_model
    data["system_version"] = system_version
    data["app_version"] = app_version
    save_account_data(phone_number, data)
    logger.info("%s: assigned new device/app_version: %s | %s | %s", phone_number, device_model, system_version, app_version)
    return device_model, system_version, app_version

# ============================================================
# 🧩 ساخت کلاینت از JSON
# ============================================================
def _make_client_from_json(phone_number: str) -> Optional[Client]:
    try:
        data_path = os.path.join(ACCOUNTS_DATA_FOLDER, f"{phone_number}.json")
        if not os.path.exists(data_path):
            logger.error(f"{phone_number}: ⚠️ Account JSON not found → {data_path}")
            return None

        with open(data_path, "r", encoding="utf-8") as f:
            account_data = json.load(f)

        session_base = account_data.get("session")
        if not session_base:
            logger.error(f"{phone_number}: Missing 'session' key in JSON → {data_path}")
            return None

        session_path = os.path.join(ACCOUNTS_FOLDER, session_base)
        if not session_path.endswith(".session"):
            session_path += ".session"

        os.makedirs(os.path.dirname(session_path), exist_ok=True)
        api_id = account_data.get("api_id")
        api_hash = account_data.get("api_hash")
        if not api_id or not api_hash:
            logger.error(f"{phone_number}: Missing API credentials in JSON → {data_path}")
            return None

        # دریافت یا تخصیص device/system/app_version پایدار
        device_model, system_version, app_version = get_or_assign_device_for_account(phone_number)

        cli = Client(
            name=session_path.replace(".session", ""),
            api_id=int(api_id),
            api_hash=str(api_hash),
            sleep_threshold=30,
            workdir=os.path.join("acc_temp", phone_number),
            no_updates=True,
            device_model=device_model,
            system_version=system_version,
            app_version=app_version
        )

        if account_data.get("2fa_password"):
            setattr(cli, "_twofa_password", account_data["2fa_password"])

        logger.debug("%s: Client prepared (%s | %s | %s)", phone_number, device_model, system_version, app_version)
        return cli

    except Exception as e:
        tb = traceback.format_exc(limit=3)
        logger.critical(f"{phone_number}: 💥 Error creating client - {type(e).__name__}: {e}\n{tb}")
        return None

# ============================================================
# 🧠 ساخت یا دریافت کلاینت فعال
# ============================================================
async def get_or_start_client(phone_number: str) -> Optional[Client]:
    cli = client_pool.get(phone_number)
    try:
        # اگر از قبل وصل است
        if cli is not None and getattr(cli, "is_connected", False):
            logger.debug(f"{phone_number}: Already connected → {getattr(cli, 'name', '<unknown>')}")
            return cli

        # ساخت کلاینت جدید
        cli = _make_client_from_json(phone_number)
        if cli is None:
            logger.error(f"{phone_number}: ❌ Could not build client (no JSON or invalid data)")
            return None

        # مسیر فایل سشن با توجه به نسخه Pyrogram
        try:
            session_db_path = getattr(cli, "storage", None)
            if session_db_path and hasattr(cli.storage, "session_file"):
                session_db_path = cli.storage.session_file  # Pyrogram 2.x
            else:
                session_db_path = f"{cli.name}.session"  # fallback
        except Exception:
            session_db_path = f"{cli.name}.session"

        # بررسی وجود فایل سشن
        if not os.path.exists(session_db_path):
            logger.warning(f"{phone_number}: Session file not found → {session_db_path}")

        # شروع کلاینت
        try:
            await cli.start()
            await asyncio.sleep(0.4)
            logger.info(f"{phone_number}: ✅ Client started successfully.")
        except errors.SessionPasswordNeeded:
            twofa = getattr(cli, "_twofa_password", None)
            if twofa:
                await cli.check_password(twofa)
                logger.info(f"{phone_number}: ✅ 2FA password applied.")
            else:
                logger.error(f"{phone_number}: ⚠️ 2FA required but missing.")
                return None
        except errors.AuthKeyDuplicated:
            logger.error(f"{phone_number}: ❌ AuthKeyDuplicated (session invalid).")
            return None
        except Exception as e:
            tb = traceback.format_exc(limit=3)
            logger.error(f"{phone_number}: ❌ Start failed - {type(e).__name__}: {e}\n{tb}")
            return None

        # افزودن به pool
        client_pool[phone_number] = cli
        client_locks.setdefault(phone_number, asyncio.Lock())
        return cli

    except Exception as e:
        tb = traceback.format_exc(limit=3)
        logger.critical(f"{phone_number}: 💥 Fatal error in get_or_start_client - {type(e).__name__}: {e}\n{tb}")
        return None

# ============================================================
# 🚀 Preload با لاگ کامل
# ============================================================
def accounts() -> List[str]:
    accs: Set[str] = set()
    if not os.path.isdir(ACCOUNTS_FOLDER):
        return []
    for acc in os.listdir(ACCOUNTS_FOLDER):
        full = os.path.join(ACCOUNTS_FOLDER, acc)
        if os.path.isfile(full) and acc.endswith(".session"):
            accs.add(acc.split(".")[0])
    return list(accs)

def get_active_accounts() -> Set[str]:
    return set(accounts())

async def preload_clients(limit: Optional[int] = None) -> None:
    phones = list(get_active_accounts())
    if limit is not None:
        phones = phones[:max(0, int(limit))]

    if not phones:
        logger.info("⚙️ No accounts found for preload.")
        return

    logger.info(f"🚀 Preloading {len(phones)} clients...")
    ok, bad = 0, 0

    for idx, phone in enumerate(phones, 1):
        logger.info(f"🔹 [{idx}/{len(phones)}] Loading client {phone}")
        try:
            cli = await get_or_start_client(phone)
            if cli and getattr(cli, "is_connected", False):
                ok += 1
                logger.info(f"{phone}: ✅ Connected.")
            else:
                bad += 1
                logger.warning(f"{phone}: ❌ Not connected after start().")
        except Exception as e:
            bad += 1
            tb = traceback.format_exc(limit=3)
            logger.error(f"{phone}: ❌ Exception during preload - {type(e).__name__}: {e}\n{tb}")

        await asyncio.sleep(1.0)

    logger.info(f"🎯 Preload completed: OK={ok} | FAIL={bad}")

# ============================================================
# 🧹 توقف تمام کلاینت‌ها
# ============================================================
async def stop_all_clients() -> None:
    logger.info("🧹 Stopping all clients...")
    for phone, cli in list(client_pool.items()):
        try:
            await cli.stop()
            logger.info(f"{phone}: 📴 Stopped successfully.")
        except Exception as e:
            tb = traceback.format_exc(limit=2)
            logger.warning(f"{phone}: ⚠️ Error stopping client - {type(e).__name__}: {e}\n{tb}")
        finally:
            client_pool.pop(phone, None)
            await asyncio.sleep(0.3)
    logger.info("✅ All clients stopped cleanly.")

# ============================================================
# 🧩 حذف کلاینت از pool
# ============================================================
def remove_client_from_pool(phone_number: str):
    cli = client_pool.get(phone_number)
    if cli:
        try:
            asyncio.create_task(cli.stop())
        except Exception:
            pass
        client_pool.pop(phone_number, None)
        client_locks.pop(phone_number, None)
        logger.info(f"{phone_number}: removed from pool.")

async def get_any_client(message=None, max_attempts: int = 3) -> Optional[object]:
    """
    تلاش برای گرفتن یک کلاینت فعال از بین اکانت‌ها.
    - تا `max_attempts` بار با اکانت‌های تصادفی امتحان می‌کند.
    - اگر بعد از تلاش‌ها موفق نشد، پیام خطا (در صورت وجود message) ارسال می‌کند،
      سپس stop_all_clients() فراخوانی می‌شود و در نهایت None برمی‌گردد.

    پارامترها:
      - message: (اختیاری) شی پیام pyrogram که اگر پاس داده شود، در صورت خطا ریپلای می‌کند.
      - max_attempts: تعداد دفعات تلاش (پیش‌فرض 3).
    """
    acc_list = get_active_accounts()
    if not acc_list:
        if message:
            try:
                await message.reply("⚠️ هیچ اکانت فعالی برای اتصال وجود ندارد.")
            except Exception:
                pass
        logger.warning("⚠️ هیچ اکانت فعالی در دسترس نیست.")
        return None

    tried = set()

    for attempt in range(1, max_attempts + 1):
        # اگر همه‌ی اکانت‌ها امتحان شده‌اند، از حلقه خارج شو
        if len(tried) == len(acc_list):
            break

        # انتخاب تصادفی از بین اکانت‌هایی که هنوز امتحان نشده‌اند
        phone = random.choice([p for p in acc_list if p not in tried])
        tried.add(phone)
        logger.info(f"🔁 تلاش {attempt}/{max_attempts} برای اتصال با اکانت {phone}")

        try:
            cli = await get_or_start_client(phone)

            # اگر کلاینت برگشت و به نظر متصل است، برگردان
            if cli and getattr(cli, "is_connected", True):
                logger.info(f"✅ اتصال موفق با اکانت {phone}")
                return cli
            else:
                logger.warning(f"⚠️ اکانت {phone} وصل نیست یا کلاینت معتبری برنگشته.")
        except Exception as e:
            logger.error(f"❌ خطا در اتصال {phone}: {type(e).__name__} - {e}")
            # فاصله کوتاه بین تلاش‌ها تا فشار به منابع کمتر شود
            try:
                await asyncio.sleep(1)
            except Exception:
                pass

    # اگر بعد از تلاش‌ها موفق نشد
    error_msg = f"❌ هیچ کلاینت فعالی پس از {max_attempts} تلاش یافت نشد. در حال ریست کامل کلاینت‌ها..."
    if message:
        try:
            await message.reply(error_msg)
        except Exception:
            pass
    logger.error(error_msg)

    try:
        await stop_all_clients()
        logger.warning("🔄 تمام کلاینت‌ها ریست شدند (stop_all_clients فراخوانی شد).")
    except Exception as e:
        logger.error(f"⚠️ خطا در ریست کلاینت‌ها: {type(e).__name__} - {e}")

    return None