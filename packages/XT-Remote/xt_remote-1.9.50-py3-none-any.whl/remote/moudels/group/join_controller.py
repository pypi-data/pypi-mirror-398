# remote/join_controller.py
import logging
from . import joiner
from ..account.client import client_manager
logger = logging.getLogger(__name__)

async def handle_join_cmd(message):
    """
    فرمان /join
    تمام اکانت‌ها را به لینک داده‌شده عضو می‌کند.
    """
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("لینک عضویت را بده (مثلاً: join https://t.me/Example)")
            return

        link = parts[1].strip()
        acc_list = client_manager.accounts()

        if not acc_list:
            await message.reply("هیچ اکانتی یافت نشد.")
            return

        success, failed = await joiner.join_all(
            acc_list,
            link,
            client_manager.get_or_start_client
        )

        await message.reply(f"🎯 Join Summary:\n✅ موفق: {success}\n❌ ناموفق: {failed}")

    except Exception as e:
        logger.exception(f"join_command error: {e}")
        await message.reply(f"خطا در دستور join: {e}")
