# antispam_core/profile_media.py
import os, asyncio, logging
from pyrogram import errors
from ..client.client_manager import accounts, get_or_start_client

logger = logging.getLogger(__name__)

async def change_profile_photo(app, message):
    try:
        if not message.reply_to_message or not message.reply_to_message.photo:
            await message.reply('لطفا به یک عکس ریپلای کنید')
            return

        accs = accounts()
        if not accs:
            await message.reply('هیچ اکانتی برای تغییر عکس وجود ندارد')
            return

        photo_path = await app.download_media(message.reply_to_message.photo.file_id, file_name=f'temp_photo_{message.id}.png')
        success = 0
        for acc in accs:
            try:
                cli = await get_or_start_client(acc)
                if cli:
                    await cli.set_profile_photo(photo=photo_path)
                    success += 1
            except Exception as e:
                logger.warning(f"{acc}: set_profile_photo failed {e}")
        try:
            os.remove(photo_path)
        except:
            pass
        await message.reply(f'تغییر عکس پروفایل انجام شد. موفق: {success}/{len(accs)}')
    except Exception as e:
        await message.reply(f'خطا در تغییر عکس پروفایل: {str(e)}')


async def delete_all_profile_photos(message):
    try:
        accs = accounts()
        if not accs:
            await message.reply('هیچ اکانتی وجود ندارد')
            return
        success = 0
        for acc in accs:
            try:
                cli = await get_or_start_client(acc)
                photos = [p async for p in cli.get_chat_photos("me")]
                if photos:
                    await cli.delete_profile_photos([p.file_id for p in photos])
                    success += 1
                await asyncio.sleep(1)
            except Exception:
                pass
        await message.reply(f'حذف عکس‌ها انجام شد. موفق: {success}/{len(accs)}')
    except Exception as e:
        await message.reply(f'خطای کلی در حذف پروفایل‌ها: {str(e)}')
