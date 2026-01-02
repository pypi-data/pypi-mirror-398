# antispam_core/caption_manager.py
import logging
logger = logging.getLogger(__name__)

async def show_caption_cmd(message, spam_config: dict):
    try:
        cap = spam_config.get('caption', '')
        await message.reply(f"Caption : \n{cap if cap else '(خالی)'}")
    except Exception as e:
        await message.reply(f'خطا در نمایش کپشن: {e}')

async def add_caption_cmd(message, spam_config: dict):
    try:
        caption = message.text.replace('cap', '').strip()
        spam_config['caption'] = caption
        await message.reply('کپشن اضافه شد')
    except Exception as e:
        await message.reply(f'خطا در اضافه کردن کپشن: {e}')

async def clear_caption_cmd(message, spam_config: dict):
    try:
        spam_config['caption'] = ''
        await message.reply('کپشن حذف شد')
    except Exception as e:
        await message.reply(f'خطا در حذف کپشن: {e}')
