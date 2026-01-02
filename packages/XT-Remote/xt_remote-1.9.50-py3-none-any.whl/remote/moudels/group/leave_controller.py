# antispam_core/leave_controller.py
import logging
from . import lefter
from ..account.client import client_manager
logger = logging.getLogger(__name__)

async def handle_leave_cmd(message):
    """
    فرمان /leave
    تمام اکانت‌ها را از چت موردنظر خارج می‌کند.
    """
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("آیدی یا لینک چت موردنظر را بده (مثلاً: leave https://t.me/ExampleGroup)")
            return

        chat_ref = parts[1].strip()
        acc_list = client_manager.accounts()

        if not acc_list:
            await message.reply("❌ هیچ اکانتی یافت نشد.")
            return

        success, failed = await lefter.leave_all(
            acc_list,
            chat_ref,
            client_manager.get_or_start_client
        )

        await message.reply(f"👋 Leave Summary:\n✅ موفق: {success}\n❌ ناموفق: {failed}")

    except Exception as e:
        logger.exception(f"leave_command error: {e}")
        await message.reply(f"خطا در دستور leave: {e}")
