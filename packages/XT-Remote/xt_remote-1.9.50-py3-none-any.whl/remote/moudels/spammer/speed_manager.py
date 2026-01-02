# antispam_core/speed_manager.py
import logging
from ..core import config

logger = logging.getLogger(__name__)

async def set_speed_cmd(message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("❌ لطفاً عدد فاصله زمانی را وارد کنید.\nمثال: /speed 3.5")
            return

        val = float(parts[1])
        if val <= 0:
            raise ValueError("time must be positive")

        config.spam_config['TimeSleep'] = val
        await message.reply(f"✅ فاصله زمانی ارسال‌ها به {val} ثانیه تغییر یافت.")
        logger.info(f"TimeSleep updated to {val}s")

    except ValueError:
        await message.reply("❌ عدد وارد شده نامعتبر است. مثال: /speed 2.5")
    except Exception as e:
        logger.error(f"Error setting speed: {e}")
        await message.reply(f"⚠️ خطا در تنظیم سرعت: {e}")
