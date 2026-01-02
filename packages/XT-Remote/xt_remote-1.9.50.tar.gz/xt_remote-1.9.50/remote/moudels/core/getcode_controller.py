# antispam_core/getcode_controller.py
import os, logging 
from ..account.client.client_manager import get_active_accounts, get_or_start_client
logger = logging.getLogger(__name__)

async def handle_getcode_cmd(message):
    """
    فرمان /gcode
    پیام آخر از 777000 را از سشن اکانت خواسته‌شده می‌خواند.
    """
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply('لطفا شماره را وارد کنید\nمثال: gcode +989123456789')
            return
        accs = list(get_active_accounts())
        number = parts[1]
        session_path = f'acc/{number}.session'
        if not os.path.exists(session_path):
            await message.reply('<b>شماره مورد نظر وجود ندارد.</b>')
            return
        for phone in accs:
            if phone == number:
                try:
                    cli = await get_or_start_client(phone)
                    if cli and getattr(cli, "is_connected", False):
                        logger.info("get_any_client: started %s", phone)
                        
                except Exception as e:
                    logger.warning("get_any_client: failed start %s: %s: %s", phone, type(e).__name__, e)
                break
            else:
                logger.info(f"{phone}")
                
        code_message = ''
        try:
                messages = [msg async for msg in cli.get_chat_history(777000, limit=1)]
                if messages and messages[0].text:
                    code_message = messages[0].text
                else:
                    code_message = 'هیچ پیامی از تلگرام دریافت نشد'                    
        except Exception as e:
            logger.error(f"Error while reading code for {number}: {e}")
            await message.reply(f'<b>هنگام فراخوانی سشن خطایی رخ داد:</b>\n{str(e)}')
        if code_message:
            await message.reply(code_message)
        
    except Exception as e:
        logger.error(f"getcode unknown error: {e}")
        await message.reply(f'<b>خطای ناشناخته:</b> {str(e)}')
