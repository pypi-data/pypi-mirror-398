from pyrogram import filters, errors
from pyrogram.types import Message
from ..moudels.admin.admin_manager import admin_filter, owner_filter
from ..moudels.account import account_manager, account_viewer, cleaner
from ..moudels.account.client import client_manager
from ..moudels.account.profile import profile_info, profile_media, profile_privacy, username_manager
from ..moudels.admin import admin_manager
from ..moudels.analytics import analytics_manager as analytics 
from ..moudels.batch import batch_manager
from ..moudels.core import config, restart_module, getcode_controller, help_menu
from ..moudels.db import db_monitor, sqlite_utils
from ..moudels.group import join_controller, leave_controller
from ..moudels.spammer import spammer, speed_manager, stop_manager
from ..moudels.text import caption_manager, mention_manager, text_manager
from ..moudels.utils import block_manager, file_sender 
from .metadata import COMMANDS, CommandMeta
from ..moudels.core.config import spam_config
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

runner = 0


def register_commands(app):

    # =========================
    #  ACCOUNT COMMANDS
    # =========================
    async def add_account(client, message: Message):
        await account_manager.add_account_cmd(message, account_manager.get_app_info)

    async def set_code(client, message: Message):
        await account_manager.set_code_cmd(message)

    async def set_2fa(client, message: Message):
        await account_manager.set_2fa_cmd(message)

    async def delete_account(client, message: Message):
        await account_manager.delete_account_cmd(message)

    async def delete_all_accounts(client, message: Message):
        await account_manager.delete_all_accounts_cmd(message)

    async def list_accounts(client, message: Message):
        await account_viewer.list_accounts_cmd(message)

    async def give_data_sessions_handler(client, message: Message):
        await file_sender.give_data_sessions_cmd(app, message)

    async def del_all_pv_gp_ch_en(client, message: Message):
        await cleaner.del_all_pv_gp_ch_en_cmd(message)

    async def give_sessions_handler(client, message: Message):
        await file_sender.give_sessions_cmd(app, message)

    # =========================
    #  TEXT / CAPTION
    # =========================
    async def save_text(client, message: Message):
        await text_manager.save_text_cmd(message)

    async def clear_texts(client, message: Message):
        await text_manager.clear_texts_cmd(message)

    async def show_text(client, message: Message):
        await text_manager.show_texts_cmd(message)

    async def show_caption(client, message: Message):
        await caption_manager.show_caption_cmd(message,spam_config)

    async def add_caption(client, message: Message):
        await caption_manager.add_caption_cmd(message,spam_config)

    async def clear_caption(client, message: Message):
        await caption_manager.clear_caption_cmd(message,spam_config)

    # =========================
    #  MENTION MANAGEMENT
    # =========================
    async def _setmention(client, m: Message):
        # /textmention <متن منشن>
        txt = m.text.split(None, 1)[1] if (m.text and len(m.command) > 1) else ""
        await m.reply(await mention_manager.set_mention_text(txt))

    async def _mention_user(client, m: Message):
        # /mention_user <user_id>  یا ریپلای
        user_id = None
        if len(m.command) > 1:
            user_id = m.command[1]
        elif m.reply_to_message and m.reply_to_message.from_user:
            user_id = m.reply_to_message.from_user.id

        if not user_id:
            return await m.reply("❗ روی پیام فرد هدف ریپلای بزن یا آیدی را بعد از دستور بنویس.")

        await m.reply(await mention_manager.set_mention_user(user_id))

    async def _mention_toggle(client, m: Message):
        # /mention_toggle on|off
        if len(m.command) < 2:
            return await m.reply("Usage: /mention_toggle <on|off>")
        arg = m.command[1].lower()
        if arg not in ("on", "off"):
            return await m.reply("Usage: /mention_toggle <on|off>")
        enabled = arg == "on"
        await m.reply(await mention_manager.toggle_mention(enabled))

    async def _mention_group_toggle(client, m: Message):
        # /mention_group_toggle on|off
        if len(m.command) < 2:
            return await m.reply("Usage: /mention_group_toggle <on|off>")
        arg = m.command[1].lower()
        if arg not in ("on", "off"):
            return await m.reply("Usage: /mention_group_toggle <on|off>")
        enabled = arg == "on"
        await m.reply(await mention_manager.toggle_group_mention(enabled))

    async def _mention_gps(client, m: Message):
        # /mention_gps <id|@user|link> ...
        if not (m.text and len(m.command) > 1):
            return await m.reply("Usage: /mention_gps <id1> <id2> ...")
        tokens = m.command[1:]
        ids = await mention_manager._resolve_many_tokens_to_ids(client, tokens)
        if not ids:
            return await m.reply("❌ هیچ شناسهٔ معتبری تشخیص داده نشد.")
        msg = await mention_manager.add_groups_by_ids(*ids)
        await m.reply(msg)

    async def _mention_del(client, m: Message):
        # /mention_del <id|@user|link> ...
        if not (m.text and len(m.command) > 1):
            return await m.reply("Usage: /mention_del <id1> <id2> ...")
        tokens = m.command[1:]
        ids = await mention_manager._resolve_many_tokens_to_ids(client, tokens)
        if not ids:
            return await m.reply("❌ هیچ شناسهٔ معتبری برای حذف تشخیص داده نشد.")
        msg = await mention_manager.remove_groups_by_ids(*ids)
        await m.reply(msg)

    async def _mention_clear(client, m: Message):
        await m.reply(await mention_manager.clear_groups())

    async def _mention_status(client, m: Message):
        await m.reply(await mention_manager.mention_status())

    # =========================
    #  GETCODE / RESTART / JOIN / LEAVE
    # =========================
    async def get_code_command(client, message: Message):
        await getcode_controller.handle_getcode_cmd(message, account_manager.get_app_info)

    async def restart_cmd(client, message: Message):
        restart_module.clear_logs()
        await message.reply("🔄 عملیات ریست کامل شد!")

    async def join_command(client, message: Message):
        await join_controller.handle_join_cmd(message)

    async def leave_command(client, message: Message):
        await leave_controller.handle_leave_cmd(message)

    # =========================
    #  ADMIN MANAGEMENT
    # =========================
    async def add_admin(client, message: Message):
        await admin_manager.add_admin_cmd(message)

    async def del_admin(client, message: Message):
        await admin_manager.del_admin_cmd(message)

    async def list_admins(client, message: Message):
        await admin_manager.list_admins_cmd(message)

    # =========================
    #  PROFILE SETTINGS
    # =========================
    async def profilesettings_cmd(client, message: Message):
        await profile_privacy.profile_settings_cmd(message)

    async def set_profile_photo_cmd(client, message: Message):
        await profile_media.change_profile_photo(app, message)

    async def delete_all_photos_cmd(client, message: Message):
        await profile_media.delete_all_profile_photos(message)

    async def change_name_cmd(client, message: Message):
        await profile_info.change_name_cmd(message)

    async def change_bio_cmd(client, message: Message):
        await profile_info.change_bio_cmd(message)

    async def set_username_cmd(client, message: Message):
        await username_manager.set_usernames_for_all(message)

    async def rem_username_cmd(client, message: Message):
        await username_manager.remove_usernames_for_all(message)

    # =========================
    #  BLOCK / UNBLOCK
    # =========================
    async def block_user_all_accounts(client, message: Message):
        await block_manager.block_user_all_cmd(message)

    async def unblock_user_all_accounts(client, message: Message):
        await block_manager.unblock_user_all_cmd(message)

    # =========================
    #  DB
    # =========================
    async def cmd_db_status(client, message: Message):
        await db_monitor.db_status_cmd(message)

    async def cmd_db_repair(client, message: Message):
        await db_monitor.db_repair_cmd(message)

    # =========================
    #  SPAMMER
    # ========================= 
    async def start_spam(client, message: Message):
        # فرم فعلی: spam <target>
        if len(message.command) < 2:
            await message.reply("❌ لطفاً لینک یا آیدی هدف را وارد کنید.")
            return

        raw_target = message.command[1].strip()
        config.spam_config["run"] = False
        target_chat_id = None

        # تشخیص نوع هدف (آیدی عددی / اینوایت / یوزرنیم / ...)
        ttype, tval, aux = spammer._normalize_target_for_spam(raw_target)
        try:
            # 1) آیدی عددی آماده
            if ttype == "chat_id":
                target_chat_id = int(tval)
                await message.reply(f"🧩 آیدی عددی شناسایی شد: `{target_chat_id}`")

            # 2) لینک اینوایت (مثل https://t.me/+HASH یا joinchat/...)
            elif ttype == "invite":
                invite_link = tval

                # استفاده از اکانت‌ها برای جوین
                phones = client_manager.accounts()
                if not phones:
                    await message.reply("❌ هیچ اکانت کاربری (session) برای جوین با لینک دعوت پیدا نشد.")
                    return

                join_ok = False

                for phone in phones:
                    cli = await client_manager.get_or_start_client(phone)
                    if not cli:
                        continue

                    try:
                        chat = await cli.join_chat(invite_link)
                        target_chat_id = chat.id
                        join_ok = True
                        await message.reply(
                            f"✅ اکانت {phone} با دعوت‌نامه جوین شد.\n"
                            f"🎯 آیدی هدف: `{target_chat_id}`"
                        )
                        break

                    except errors.UserAlreadyParticipant:
                        # این اکانت قبلاً عضو بوده، فقط آیدی را می‌گیریم
                        chat = await cli.get_chat(invite_link)
                        target_chat_id = chat.id
                        join_ok = True
                        await message.reply(
                            f"🔗 اکانت {phone} قبلاً عضو بود؛ آیدی استخراج شد: `{target_chat_id}`"
                        )
                        break

                    except errors.FloodWait as e:
                        # این اکانت FloodWait خورده، می‌ریم سراغ بعدی
                        await message.reply(
                            f"⏰ FloodWait {e.value}s روی اکانت {phone}؛ اکانت بعدی امتحان می‌شود…"
                        )
                        continue

                    except Exception as e:
                        logger.exception("Error joining invite with account %s: %s", phone, e)
                        continue

                if not join_ok or not target_chat_id:
                    await message.reply("❌ نتوانستم با هیچ اکانتی با این لینک جوین بشوم.")
                    return

            # 3) یوزرنیم / لینک عمومی (t.me/username)
            elif ttype == "username":
                username = tval
                chat = await client.get_chat(username)
                target_chat_id = chat.id
                await message.reply(f"🔍 آیدی چت پیدا شد: `{target_chat_id}`")

            else:
                await message.reply("❌ هدف نامعتبر است.")
                return

            # وقتی target_chat_id مشخص شد → اسپمر را راه می‌اندازیم
            config.spam_config["spamTarget"] = target_chat_id
            config.spam_config["run"] = True
            global runner
            await message.reply(f"🚀 اسپمر شروع شد!\n🎯 هدف نهایی: `{target_chat_id}`")

            runner = spammer.SpammerThreadingRunner(
                config.spam_config,
                client_manager.remove_client_from_pool,
            )
            runner.start()

        except Exception as e:
            logger.exception(f"Error in /spam: {e}")
            await message.reply(
                f"💥 خطا در پردازش دستور spam: `{type(e).__name__}` - {e}"
            )

    async def stop_spam(client, message: Message):
        global runner
        config.spam_config["run"] = False
        try:
            if runner:
                runner.stop()
                runner = 0
                await message.reply("🛑 اسپمر متوقف شد.")
            else:
                await message.reply("ℹ️ اسپمر فعال نبود.")
        except Exception as e:
            logger.exception(f"Error while stopping spammer: {e}")
            await message.reply("⚠ خطایی در توقف اسپمر رخ داد.")

    # =========================
    #  SPEED / BATCH / STATS
    # =========================
    async def set_speed(client, message: Message):
        await speed_manager.set_speed_cmd(message)

    async def _set_handler(client, message: Message):
        await batch_manager._set_batch_size_cmd(client, message)

    async def show_stats(client, message: Message):
        """
        /stats
        /stats <target>

        اگر آرگومان نداشته باشد → استات کل
        اگر آرگومان داشته باشد → استات فقط برای همان تارگت
        """
        try:
            args = message.command[1:] if getattr(message, "command", None) else []
            target = args[0] if args else None

            # فرض: analytics.show_stats_cmd(message, target=None)
            # خودش رپلای را انجام می‌دهد.
            # await analytics.show_stats_cmd(message, target)
            pass

        except TypeError:
            # در صورتی که امضای تابع قدیمی باشد و فقط (message) را بگیرد
            # await analytics.show_stats_cmd(message)
            pass
        except Exception as e:
            logger.exception("Error in stats command: %s", e)
            try:
                await message.reply("💥 خطا در پردازش دستور stats رخ داد.")
            except Exception:
                pass

    # =========================
    #  COMMAND MAPPING
    # =========================
    COMMAND_HANDLERS = {
        "add": add_account,
        "code": set_code,
        "pass": set_2fa,
        "del": delete_account,
        "delall": delete_all_accounts,
        "listacc": list_accounts,

        "givedatasessions": give_data_sessions_handler,
        "delallpvgpchenl": del_all_pv_gp_ch_en,
        "givesessions": give_sessions_handler,

        "text": save_text,
        "ctext": clear_texts,
        "shtext": show_text,
        "shcap": show_caption,
        "cap": add_caption,
        "ccap": clear_caption,

        "textmention": _setmention,
        "mention_user": _mention_user,
        "mention_toggle": _mention_toggle,
        "mention_group_toggle": _mention_group_toggle,
        "mention_gps": _mention_gps,
        "mention_del": _mention_del,
        "mention_clear": _mention_clear,
        "mention_status": _mention_status,

        "gcode": get_code_command,
        "restart": restart_cmd,

        "join": join_command,
        "leave": leave_command,

        "addadmin": add_admin,
        "deladmin": del_admin,
        "admins": list_admins,

        "profilesettings": profilesettings_cmd,
        "setPic": set_profile_photo_cmd,
        "delallprofile": delete_all_photos_cmd,
        "name": change_name_cmd,
        "bio": change_bio_cmd,
        "username": set_username_cmd,
        "remusername": rem_username_cmd,

        "block": block_user_all_accounts,
        "unblock": unblock_user_all_accounts,

        "dbstatus": cmd_db_status,
        "dbrepair": cmd_db_repair,

        "spam": start_spam,
        "stop": stop_spam,
        "speed": set_speed,
        "set": _set_handler,
        "stats": show_stats,
    }

    # =========================
    #  ACCESS CHECK
    # =========================
    async def _has_access(message: Message, meta: CommandMeta) -> bool:
        """
        بر اساس metadata.py تشخیص می‌دهد کاربر اجازهٔ اجرای این کامند را دارد یا نه.
        """
        user = getattr(message, "from_user", None)
        if user is None:
            return False

        uid = int(user.id)

        owner_ids = getattr(config, "OWNER_ID", [])
        try:
            owner_ids = set(owner_ids)
        except TypeError:
            owner_ids = {owner_ids}

        admins = getattr(admin_manager, "ADMINS", set())
        try:
            admins = set(admins)
        except TypeError:
            admins = {admins}

        if meta.access == "owner":
            return uid in owner_ids

        # admin: هر کسی که ادمین است یا owner
        return uid in admins or uid in owner_ids

    # =========================
    #  ROUTER
    # =========================
    @app.on_message(
        filters.command(list(COMMANDS.keys()), prefixes=["", "/", "!", "."])
    )
    async def command_router(client, message: Message):
        if not getattr(message, "command", None):
            return

        cmd_raw = message.command[0]
        cmd = cmd_raw.lstrip("/").lower()

        meta = COMMANDS.get(cmd)
        if meta is None:
            logger.warning("Received unknown command %r in router", cmd)
            return

        if not await _has_access(message, meta):
            try:
                await message.reply("⛔️ شما اجازهٔ استفاده از این دستور را ندارید.")
            except Exception:
                pass
            return

        handler = COMMAND_HANDLERS.get(cmd)
        if handler is None:
            logger.warning("No handler mapped for command %r", cmd)
            try:
                await message.reply("⚠ این دستور فعلاً در دسترس نیست.")
            except Exception:
                pass
            return

        try:
            await handler(client, message)
        except Exception as e:
            logger.exception("Error while handling command %r: %s", cmd, e)
            try:
                await message.reply("💥 خطایی در پردازش دستور رخ داد.")
            except Exception:
                pass
