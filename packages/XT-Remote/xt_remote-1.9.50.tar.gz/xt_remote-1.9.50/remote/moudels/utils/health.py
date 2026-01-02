# import random, asyncio, logging
# from pyrogram import errors
# logger = logging.getLogger(__name__)

# async def check_account_health(phone, client):
#     """چک سلامت کلی هر اکانت"""
#     try:
#         if not client.is_connected:
#             await client.start()
#         me = await client.get_me()
#         return bool(me)
#     except (errors.UserDeactivated, errors.AuthKeyUnregistered, errors.UserDeactivatedBan):
#         logger.warning(f"{phone} is deactivated/banned.")
#         return False
#     except Exception as e:
#         logger.error(f"Error checking health for {phone}: {e}")
#         return False

# async def replace_problematic_account(phone, bot_data):
#     """جایگزینی خودکار اکانت خراب"""
#     inactive = [p for p in bot_data.accounts if p not in bot_data.active_accounts]
#     if not inactive:
#         logger.warning("No inactive accounts to replace.")
#         return None
#     replacement = random.choice(inactive)
#     if phone in bot_data.active_accounts:
#         bot_data.active_accounts.remove(phone)
#     bot_data.active_accounts.add(replacement)
#     bot_data.save_to_file()
#     logger.info(f"♻️ Replaced {phone} with {replacement}")
#     return replacement
