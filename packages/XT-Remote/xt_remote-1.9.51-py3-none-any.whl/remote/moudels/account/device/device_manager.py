# antispam_core/device_manager.py (updated safe version)
import asyncio, logging
from pyrogram import Client, errors, raw
from ..client.client_manager import get_or_start_client, accounts
from ..account_manager import get_account_data


logger = logging.getLogger(__name__)

async def _ensure_2fa_if_needed(cli: Client, phone_number: str):
    """در صورت نیاز، پسورد دو مرحله‌ای را اعمال می‌کند."""
    try:
        await cli.invoke(raw.functions.account.GetAuthorizations())
        return
    except errors.SessionPasswordNeeded:
        pass
    except Exception:
        return

    data = get_account_data(phone_number) or {}
    pw = data.get("2fa_password")
    if pw:
        try:
            await cli.check_password(pw)
        except Exception as e:
            logger.warning(f"2FA check failed for {phone_number}: {e}")


async def _list_authorizations(cli: Client):
    """برمی‌گرداند: (authorizations, web_authorizations)"""
    try:
        auths = await cli.invoke(raw.functions.account.GetAuthorizations())
        web_auths = await cli.invoke(raw.functions.account.GetWebAuthorizations())
        return getattr(auths, "authorizations", []), getattr(web_auths, "authorizations", [])
    except Exception:
        try:
            auths = await cli.invoke(raw.functions.account.GetAuthorizations())
            return getattr(auths, "authorizations", []), []
        except Exception as e:
            logger.error(f"Error listing authorizations: {e}")
            return [], []


async def terminate_all_other_sessions_cmd(message):
    """
    حذف نشست‌های غیر از فعلی + گزارش کامل دستگاه‌ها
    (نشست فعلی محفوظ می‌ماند)
    """
    acc_list = accounts()
    if not acc_list:
        await message.reply("❌ هیچ اکانتی پیدا نشد.")
        return

    lines = ["🔒 <b>شروع حذف نشست‌های اضافی (نشست فعلی حفظ می‌شود):</b>"]
    done, fail = 0, 0

    for phone in sorted(acc_list):
        try:
            cli = await get_or_start_client(phone)
            if cli is None:
                lines.append(f"• {phone}: ✖️ کلاینت در دسترس نیست")
                fail += 1
                continue

            await _ensure_2fa_if_needed(cli, phone)
            authorizations, web_authorizations = await _list_authorizations(cli)
            to_revoke = []

            # ✅ فقط نشست‌هایی حذف می‌شن که current=False
            for a in authorizations:
                try:
                    h = int(getattr(a, "hash", 0))
                    is_current = bool(getattr(a, "current", False))
                    if not is_current and h:
                        to_revoke.append(h)
                except Exception:
                    pass

            revoked, failed = 0, 0
            for h in to_revoke:
                try:
                    await cli.invoke(raw.functions.account.ResetAuthorization(hash=h))
                    revoked += 1
                    await asyncio.sleep(0.25)
                except errors.FloodWait as e:
                    await asyncio.sleep(e.value)
                except errors.SessionPasswordNeeded:
                    await _ensure_2fa_if_needed(cli, phone)
                except Exception:
                    failed += 1

            # 🌐 حذف نشست‌های وب بدون حذف نشست فعلی
            web_reset = False
            try:
                await cli.invoke(raw.functions.account.ResetWebAuthorizations())
                web_reset = True
            except errors.SessionPasswordNeeded:
                await _ensure_2fa_if_needed(cli, phone)
                try:
                    await cli.invoke(raw.functions.account.ResetWebAuthorizations())
                    web_reset = True
                except Exception:
                    web_reset = False
            except Exception:
                web_reset = False

            # 📊 گزارش باقی‌مانده‌ها
            rem_auths, rem_web = await _list_authorizations(cli)
            devices = []
            for auth in rem_auths:
                app = getattr(auth, "app_name", "Unknown")
                ip = getattr(auth, "ip", "—")
                country = getattr(auth, "country", "")
                dc_id = getattr(auth, "dc_id", "?")
                current = getattr(auth, "current", False)
                mark = "🟢" if current else "⚪️"
                devices.append(f"{mark} <b>{app}</b> ({ip}, {country}, DC{dc_id})")

            lines.append(
                f"\n📱 <b>{phone}</b>\n"
                f"✅ نشست‌های حذف‌شده: {revoked}/{len(to_revoke)}"
                f"\n🌐 وب: {'Reset' if web_reset else '—'}"
                f"\n📊 نشست‌های باقی‌مانده:\n" + ("\n".join(devices) if devices else "—")
            )

            done += 1
            await asyncio.sleep(0.5)

        except errors.FloodWait as e:
            await asyncio.sleep(e.value)
            lines.append(f"• {phone}: ⚠️ FloodWait({e.value})")
            fail += 1
        except Exception as ex:
            lines.append(f"• {phone}: ✖️ خطا: {ex}")
            fail += 1

    lines.append(f"\n📋 نتیجه نهایی:\n✅ انجام شد برای {done} | ❌ ناموفق {fail} | مجموع {len(acc_list)}")
    out = "\n".join(lines)
    if len(out) > 3900:
        out = out[:3800] + "\n... (trimmed)"

    await message.reply(out)
    logger.info("🔒 Device termination completed (current session preserved).")
