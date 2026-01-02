# antispam_core/profile_info.py
import asyncio, logging
from ..client.client_manager import accounts, get_or_start_client

logger = logging.getLogger(__name__)

async def change_name_cmd(message):
    try:
        new_name = message.text.split(' ', 1)[1].strip()
        if not new_name:
            await message.reply('نام جدید را وارد کنید')
            return
        accs = accounts()
        if not accs:
            await message.reply('No accounts available')
            return
        success = 0
        for acc in accs:
            try:
                cli = await get_or_start_client(acc)
                if cli:
                    await cli.update_profile(first_name=new_name)
                    success += 1
                await asyncio.sleep(0.8)
            except Exception as e:
                logger.warning(f"{acc}: name change failed {e}")
        await message.reply(f'Name change completed. Success: {success}/{len(accs)}')
    except Exception as e:
        await message.reply(f'Error changing names: {str(e)}')


async def change_bio_cmd(message):
    try:
        new_bio = message.text.split(maxsplit=1)[1]
        accs = accounts()
        if not accs:
            await message.reply('هیچ اکانتی برای تغییر بیو وجود ندارد')
            return
        success = 0
        for acc in accs:
            try:
                cli = await get_or_start_client(acc)
                if cli:
                    await cli.update_profile(bio=new_bio)
                    success += 1
                await asyncio.sleep(0.8)
            except Exception:
                pass
        await message.reply(f'تغییر بیو انجام شد. موفق: {success}/{len(accs)}')
    except IndexError:
        await message.reply('لطفا بیو جدید را وارد کنید')
    except Exception as e:
        await message.reply(f'خطا در تغییر بیو: {str(e)}')
