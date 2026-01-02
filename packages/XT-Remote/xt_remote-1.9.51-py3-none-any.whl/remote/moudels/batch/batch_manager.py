# antispam_core/batch_manager.py
import logging 
from ..core.config import spam_config

logger = logging.getLogger(__name__)

async def _set_batch_size_cmd(client, message):
    """تابع اصلی برای تغییر Batch Size"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("مثال: `set 3`")
            return

        val = int(parts[1])
        if val <= 0:
            await message.reply("عدد باید بزرگ‌تر از صفر باشد.")
            return

        spam_config['BATCH_SIZE'] = val
        await message.reply(f"✅ Batch size set to: {val}")
    except ValueError:
        await message.reply("فرمت نادرست. مثال: `set 3`")
    except Exception as e:
        logger.error(f"Error setting batch size: {e}")
        await message.reply(f"⚠️ خطا در تنظیم batch size: {e}")

def get_batch_size() -> int:
    """برگرداندن مقدار فعلی Batch Size"""
    return int(spam_config['BATCH_SIZE'])

