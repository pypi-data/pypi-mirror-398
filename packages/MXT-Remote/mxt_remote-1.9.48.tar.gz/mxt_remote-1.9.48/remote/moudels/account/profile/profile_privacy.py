# antispam_core/profile_privacy.py
import asyncio, logging
from pyrogram import Client, raw, errors
from ..client.client_manager import accounts, get_or_start_client

logger = logging.getLogger(__name__)


async def set_profile_photo_privacy(cli: Client, mode: int):
    if mode == 1:
        rules = [raw.types.InputPrivacyValueAllowAll()]
    elif mode == 2:
        rules = [raw.types.InputPrivacyValueAllowContacts()]
    elif mode == 3:
        rules = [raw.types.InputPrivacyValueDisallowAll()]
    else:
        raise ValueError("invalid mode (use 1|2|3)")

    return await cli.invoke(
        raw.functions.account.SetPrivacy(
            key=raw.types.InputPrivacyKeyProfilePhoto(),
            rules=rules,
        )
    )


async def profile_settings_cmd(message):
    """
    تغییر سطح حریم شخصی Profile Photo همهٔ اکانت‌ها.

    ورودی معتبر:
      profilesettings 1   → همه
      profilesettings 2   → فقط مخاطبین
      profilesettings 3   → هیچ‌کس

    قبلاً به message.command وابسته بود؛
    الان خودمان از روی message.text پارس می‌کنیم تا وابستگی کمتر و رفتار پایدارتر باشد.
    """
    try:
        text = (message.text or "").strip()
        parts = text.split()

        # parts[0] = /profilesettings یا profilesettings
        # parts[1] = عدد mode (1 / 2 / 3)
        if len(parts) < 2:
            await message.reply("مثال:\nprofilesettings 1\n1: همه | 2: مخاطبین | 3: هیچ‌کس")
            return

        raw_mode = parts[1]

        try:
            mode = int(raw_mode)
        except ValueError:
            await message.reply("عدد نامعتبر. فقط 1 یا 2 یا 3 مجاز است.")
            return

        if mode not in (1, 2, 3):
            await message.reply("عدد نامعتبر. فقط 1 یا 2 یا 3 مجاز است.")
            return

        label = {
            1: "Everybody (همه)",
            2: "My Contacts (مخاطبین)",
            3: "Nobody (هیچ‌کس)",
        }[mode]

        acc_list = accounts()
        if not acc_list:
            await message.reply("❌ هیچ اکانتی یافت نشد.")
            return

        ok = fail = 0

        for phone in acc_list:
            try:
                cli = await get_or_start_client(phone)
                if cli is None:
                    fail += 1
                    continue

                await set_profile_photo_privacy(cli, mode)
                ok += 1
                await asyncio.sleep(0.4)

            except errors.FloodWait as e:
                await asyncio.sleep(e.value)
                fail += 1

            except Exception as ex:
                logger.warning(f"privacy set failed for {phone}: {ex}")
                fail += 1

        await message.reply(
            f"تنظیم «Profile photos» روی «{label}» انجام شد.\n✅ موفق: {ok}\n❌ ناموفق: {fail}"
        )

    except Exception as e:
        await message.reply(f"خطا در اجرای profilesettings: {e}")
