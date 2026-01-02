# CliRemote/remote/account_viewer.py
import asyncio, logging, os
from pyrogram import errors
from .client.client_manager import client_pool, get_or_start_client, accounts

logger = logging.getLogger(__name__)

ACCOUNT_LIST_PATH = os.path.join(os.getcwd(), "account_list.txt")

async def list_accounts_cmd(message):
    """
    نمایش دقیق وضعیت اکانت‌ها (با حفظ اتصال‌ها)
    خروجی نهایی همیشه در account_list.txt ذخیره می‌شود و در انتها فایل ارسال می‌گردد.
    """
    try:
        acc_list = accounts()
        if not acc_list:
            text = 'لیست اکانت‌ها:\n(هیچ اکانتی وجود ندارد)'
            # ذخیره در فایل
            with open(ACCOUNT_LIST_PATH, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            # ارسال فایل
            await message.reply_document(
                document=ACCOUNT_LIST_PATH,
                caption="📋 گزارش اکانت‌ها (خالی)"
            )
            return

        lines = ['📋 <b>لیست اکانت‌ها:</b>']
        success, failed = 0, 0

        for idx, phone in enumerate(acc_list, start=1):
            try:
                # 🔹 دریافت کلاینت از pool یا ساخت مجدد
                cli = client_pool.get(phone)
                if cli is None or not getattr(cli, 'is_connected', False):
                    cli = await get_or_start_client(phone)

                # تلاش مجدد در صورت قطع بودن
                if cli is None:
                    await asyncio.sleep(0.8)
                    cli = await get_or_start_client(phone)

                if cli is None:
                    raise Exception("Client could not be started")

                # 🔁 تا دو بار تلاش برای دریافت اطلاعات
                retry = 0
                me = None
                while retry < 2:
                    try:
                        me = await cli.get_me()
                        if me:
                            break
                    except errors.FloodWait as e:
                        await asyncio.sleep(e.value)
                    except Exception:
                        retry += 1
                        await asyncio.sleep(1)

                if me:
                    success += 1
                    full_name = (me.first_name or "") + " " + (me.last_name or "")
                    full_name = full_name.strip() or "-"
                    uid = me.id
                    lines.append(f"\n<b>{idx}. {phone}</b>")
                    lines.append(f"Status : ✅ OK")
                    lines.append(f"Power  : 🟢 ON")
                    lines.append(f"Name   : {full_name}")
                    lines.append(f"UserID : <code>{uid}</code>")
                else:
                    failed += 1
                    lines.append(f"\n<b>{idx}. {phone}</b>")
                    lines.append(f"Status : ❌ ERROR")
                    lines.append(f"Power  : 🔴 OFF")
                    lines.append(f"Name   : -")
                    lines.append(f"UserID : -")

            except errors.UserDeactivated:
                failed += 1
                lines.append(f"\n<b>{idx}. {phone}</b>")
                lines.append(f"Status : 🚫 Deactivated")
                lines.append(f"Power  : 🔴 OFF")
                lines.append(f"Name   : -")
                lines.append(f"UserID : -")

            except Exception as e:
                failed += 1
                lines.append(f"\n<b>{idx}. {phone}</b>")
                lines.append(f"Status : ⚠️ Error: {str(e)[:40]}")
                lines.append(f"Power  : 🔴 OFF")
                lines.append(f"Name   : -")
                lines.append(f"UserID : -")

            await asyncio.sleep(0.5)

        total = len(acc_list)
        lines.append(f"\n📊 <b>نتیجه:</b>\n✅ سالم: {success}\n❌ خطادار: {failed}\n🔹 مجموع: {total}")

        text = "\n".join(lines)

        # ✅ همیشه ذخیره در فایل account_list.txt
        with open(ACCOUNT_LIST_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

        # ✅ ارسال فایل خروجی
        await message.reply_document(
            document=ACCOUNT_LIST_PATH,
            caption="📋 گزارش کامل اکانت‌ها"
        )

    except Exception as e:
        # اگر جایی خطا خورد، باز هم خطا را در فایل ذخیره و فایل را ارسال می‌کنیم
        err_text = f'<b>خطا در نمایش لیست اکانت‌ها:</b>\n{e}'
        try:
            with open(ACCOUNT_LIST_PATH, "w", encoding="utf-8", newline="\n") as f:
                f.write(err_text)
            await message.reply_document(
                document=ACCOUNT_LIST_PATH,
                caption="⚠️ خطا هنگام تهیه گزارش"
            )
        except Exception:
            await message.reply(err_text)
