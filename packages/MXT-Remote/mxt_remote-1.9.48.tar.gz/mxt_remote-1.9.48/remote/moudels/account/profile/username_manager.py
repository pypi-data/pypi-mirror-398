# antispam_core/username_manager.py
import asyncio, logging
from pyrogram import errors, raw
from ..client.client_manager import accounts, get_or_start_client

logger = logging.getLogger(__name__)

def _max_repeat_for_suffix(base: str, suffix: str, max_len: int = 32) -> int:
    if not suffix:
        return 0
    remain = max_len - len(base)
    return max(0, remain // len(suffix))

async def _try_set_username(cli, desired: str) -> str:
    try:
        await cli.invoke(raw.functions.account.UpdateUsername(username=desired))
        return "ok"
    except errors.UsernameNotModified:
        return "not_modified"
    except errors.UsernameOccupied:
        return "occupied"
    except errors.UsernameInvalid:
        return "invalid"
    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        return await _try_set_username(cli, desired)
    except Exception as ex:
        return f"error:{ex}"

async def set_usernames_for_all(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("مثال: `username TEST`")
        return
    base = parts[1].strip().lstrip("@")
    if not base:
        await message.reply("متن پایه نامعتبر است.")
        return

    accs = accounts()
    if not accs:
        await message.reply("❌ هیچ اکانتی پیدا نشد.")
        return

    ok, fail = 0, 0
    lines = [f"🔧 شروع ست‌کردن یوزرنیم‌ها با پایه: @{base}"]
    for idx, phone in enumerate(sorted(accs), start=1):
        digit = str(idx)
        try:
            cli = await get_or_start_client(phone)
            if cli is None:
                lines.append(f"• {phone}: ✖️ کلاینت در دسترس نیست")
                fail += 1
                continue

            max_rep = _max_repeat_for_suffix(base, digit)
            for j in range(1, max_rep + 1):
                candidate = f"{base}{digit * j}"
                status = await _try_set_username(cli, candidate)
                if status in ("ok", "not_modified"):
                    lines.append(f"• {phone}: ✅ @{candidate}")
                    ok += 1
                    break
                elif status in ("invalid", "occupied"):
                    continue
            await asyncio.sleep(0.4)
        except Exception as e:
            lines.append(f"• {phone}: ✖️ {e}")
            fail += 1

    lines.append(f"\nنتیجه: ✅ موفق {ok} / ❌ ناموفق {fail} / مجموع {len(accs)}")
    await message.reply("\n".join(lines))

async def remove_usernames_for_all(message):
    accs = accounts()
    if not accs:
        await message.reply("❌ هیچ اکانتی پیدا نشد.")
        return
    ok, fail = 0, 0
    lines = ["🧹 حذف یوزرنیم‌ها:"]
    for phone in sorted(accs):
        try:
            cli = await get_or_start_client(phone)
            await cli.invoke(raw.functions.account.UpdateUsername(username=""))
            lines.append(f"• {phone}: ✅ حذف شد")
            ok += 1
        except Exception as e:
            lines.append(f"• {phone}: ✖️ {e}")
            fail += 1
        await asyncio.sleep(0.3)
    lines.append(f"\n✅ حذف {ok} / ❌ خطا {fail}")
    await message.reply("\n".join(lines))
