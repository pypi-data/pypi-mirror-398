# remote/admin_manager.py
import json
import os
import sys
import logging
from pathlib import Path
from pyrogram import filters 
from ..core import config  

# =============================
# تنظیم logger فایل
# =============================

def _project_root() -> Path:
    """ریشه پروژه = پوشه‌ای که main.py داخلش اجرا شده. در صورت عدم دسترسی، از cwd استفاده می‌شود."""
    try:
        main_file = Path(sys.modules["__main__"].__file__).resolve()
        return main_file.parent
    except Exception:
        return Path(os.getcwd()).resolve()

_PROJECT_ROOT = _project_root()
_LOG_DIR = _PROJECT_ROOT / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_PATH = _LOG_DIR / "admins_log.txt"

# logger اختصاصی این ماژول
logger = logging.getLogger("remote.admin_manager")
logger.setLevel(logging.DEBUG)

# جلوگیری از افزودن چندباره‌ی هندلر هنگام ریلود
if not any(isinstance(h, logging.FileHandler) and getattr(h, "_admin_log", False) for h in logger.handlers):
    fh = logging.FileHandler(_LOG_PATH, encoding="utf-8")
    fh._admin_log = True  # پرچم داخلی برای تشخیص
    fh.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

logger.debug(f"Admin manager initialized. Log path: {_LOG_PATH}")

# =============================
# تنظیمات فایل ادمین‌ها
# =============================

ADMINS_FILE = "admins.json"  # اگر می‌خواهی کنار main.py باشد: ( _PROJECT_ROOT / "admins.json" ).as_posix()

def load_admins() -> list[int]:
    """
    بارگذاری لیست ادمین‌ها از فایل.
    همیشه OWNER_ID را هم به لیست اضافه می‌کند.
    """
    logger.debug(f"Loading admins from file: {ADMINS_FILE} | OWNER_ID: {config.OWNER_ID}")
    s = set(config.OWNER_ID)
    try:
        if os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"admins.json loaded. Raw: {data!r}")
                if isinstance(data, list):
                    for v in data:
                        try:
                            s.add(int(v))
                        except Exception as conv_err:
                            logger.warning(f"Skip invalid admin id in file: {v!r} | err={conv_err}")
        else:
            logger.info(f"admins.json not found at: {os.path.abspath(ADMINS_FILE)}")
    except Exception as e:
        logger.warning(f"Error loading admins: {e}", exc_info=True)

    result = sorted(s)
    logger.debug(f"Effective ADMINS after merge with OWNER_ID: {result}")
    return result


def save_admins():
    """
    ذخیره‌ی ادمین‌ها در فایل.
    """
    try:
        # نکته: در این طراحی، ADMINS شامل OWNER_ID هم می‌تواند باشد؛ مشکلی نیست
        logger.debug(f"Saving ADMINS to file: {ADMINS_FILE} | Data: {ADMINS}")
        with open(ADMINS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(ADMINS), f, ensure_ascii=False, indent=2)
        logger.info(f"Admins saved to {os.path.abspath(ADMINS_FILE)}")
    except Exception as e:
        logger.error(f"Error saving admins: {e}", exc_info=True)


ADMINS = load_admins()
logger.info(f"Loaded admins at import time: {ADMINS}")

# فیلترهای دسترسی برای Pyrogram
admin_filter = filters.create(
    lambda _, __, m: bool(getattr(m, "from_user", None)) and int(m.from_user.id) in ADMINS
)
owner_filter = filters.create(
    lambda _, __, m: bool(getattr(m, "from_user", None)) and int(m.from_user.id) in config.OWNER_ID
)

# =============================
# فرمان‌های مدیریتی
# =============================

async def add_admin_cmd(message):
    try:
        uid_display = getattr(getattr(message, "from_user", None), "id", None)
        logger.debug(f"add_admin_cmd triggered by user_id={uid_display} | text={message.text!r}")

        parts = (message.text or "").split()
        if len(parts) < 2:
            logger.debug("add_admin_cmd: missing argument")
            await message.reply("مثال: addadmin 123456789")
            return

        uid = int(parts[1])
        logger.debug(f"add_admin_cmd: parsed target uid={uid}")

        if uid in config.OWNER_ID:
            logger.info(f"add_admin_cmd: uid={uid} is OWNER; skip append")
            await message.reply("ادمین اصلی از قبل وجود دارد")
            return

        if uid not in ADMINS:
            ADMINS.append(uid)
            logger.info(f"Admin appended: {uid} | New ADMINS={sorted(ADMINS)}")
            save_admins()
            await message.reply(f"ادمین جدید اضافه شد: {uid}")
        else:
            logger.info(f"add_admin_cmd: uid={uid} already in ADMINS")
            await message.reply("قبلاً ادمین بود")
    except Exception as e:
        logger.error(f"add_admin_cmd error: {e}", exc_info=True)
        await message.reply(f"خطا: {e}")


async def del_admin_cmd(message):
    try:
        uid_display = getattr(getattr(message, "from_user", None), "id", None)
        logger.debug(f"del_admin_cmd triggered by user_id={uid_display} | text={message.text!r}")

        parts = (message.text or "").split()
        if len(parts) < 2:
            logger.debug("del_admin_cmd: missing argument")
            await message.reply("مثال: deladmin 123456789")
            return

        uid = int(parts[1])
        logger.debug(f"del_admin_cmd: parsed target uid={uid}")

        if uid in config.OWNER_ID:
            logger.info(f"del_admin_cmd: attempt to remove OWNER uid={uid} blocked")
            await message.reply("❌ امکان حذف ادمین اصلی وجود ندارد")
            return

        if uid in ADMINS:
            ADMINS.remove(uid)
            logger.info(f"Admin removed: {uid} | New ADMINS={sorted(ADMINS)}")
            save_admins()
            await message.reply(f"ادمین حذف شد: {uid}")
        else:
            logger.info(f"del_admin_cmd: uid={uid} not in ADMINS")
            await message.reply("کاربر ادمین نیست")
    except Exception as e:
        logger.error(f"del_admin_cmd error: {e}", exc_info=True)
        await message.reply(f"خطا: {e}")


async def list_admins_cmd(message):
    try:
        uid_display = getattr(getattr(message, "from_user", None), "id", None)
        logger.debug(f"list_admins_cmd triggered by user_id={uid_display}")

        if not ADMINS:
            logger.info("list_admins_cmd: ADMINS is empty")
            await message.reply("لیست ادمین‌ها خالی است.")
            return

        text = "👑 <b>ADMINS:</b>\n" + "\n".join([str(x) for x in sorted(ADMINS)])
        logger.debug(f"list_admins_cmd: respond with {len(ADMINS)} admins")
        await message.reply(text)
    except Exception as e:
        logger.error(f"list_admins_cmd error: {e}", exc_info=True)
        await message.reply(f"خطا: {e}")
