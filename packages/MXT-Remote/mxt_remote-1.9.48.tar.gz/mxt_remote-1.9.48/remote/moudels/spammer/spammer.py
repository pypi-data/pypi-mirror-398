# remote/moudels/spammer/spammer.py
"""
Real sending spammer module (asyncio-based).
- Uses build_final_text() from your project (finaly_text).
- Uses client_manager.get_or_start_client(...) to obtain Pyrogram clients.
- Controls sending rate with a per-batch (set-based) scheduler:
    ست اول  → ۲ ثانیه → ست دوم → ۲ ثانیه → ست سوم → ...
- Handles FloodWait, ChatWriteForbidden, Auth errors, timeouts and backoff.
- WARNING: This version sends real messages. Use only in your safe test group.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import re
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from pyrogram import errors

# ============================================================
# 📦 Imports (text, accounts, clients, stats)
# ============================================================
try:
    from ..text.finaly_text import build_final_text
except Exception:  # pragma: no cover
    def build_final_text(*args, **kwargs) -> str:
        # fallback تا ایمپورت نشکند
        return f"[fallback demo message] {datetime.utcnow().isoformat()}"

try:
    from ..account import account_manager  # type: ignore
except Exception:  # pragma: no cover
    account_manager = None  # type: ignore

try:
    from ..account.client import client_manager  # type: ignore
except Exception:  # pragma: no cover
    client_manager = None  # type: ignore

# 📊 stats (اختیاری؛ اگر نبود، نگذارید اسپمر بترکه)
try:
    from ..analytics_manager import update_stats  # type: ignore
except Exception:  # pragma: no cover
    def update_stats(target: Any, acc_phone: str, success: bool) -> None:  # type: ignore
        # اگر فایل analytics_manager موجود نباشد، هیچ کاری نکن
        return


# ============================================================
# 🧾 Logger setup
# ============================================================
class NanoFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        ns = int((record.created - int(record.created)) * 1_000_000_000)
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}.{ns:09d}"


logger = logging.getLogger("remote.moudels.spammer_real")
logger.setLevel(logging.INFO)

os.makedirs("logs", exist_ok=True)
_log_path = os.path.join("logs", "spammer_real.log")
_fh = logging.FileHandler(_log_path, encoding="utf-8")
_fmt = NanoFormatter("%(asctime)s - %(levelname)s - %(message)s")
_fh.setFormatter(_fmt)

# جلوگیری از دوبار اضافه‌شدن FileHandler
if not any(
    isinstance(h, logging.FileHandler)
    and getattr(h, "baseFilename", "").endswith("spammer_real.log")
    for h in logger.handlers
):
    logger.addHandler(_fh)

_ch = logging.StreamHandler()
_ch.setFormatter(_fmt)
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    logger.addHandler(_ch)

logger.info("Spammer module imported successfully.")

# ============================================================
# 🎯 Target Normalizer
# ============================================================
_INVITE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_\-]{16,}$")


def _normalize_target_for_spam(raw: str | int | None):
    """
    ورودی (لینک، یوزرنیم، آیدی عددی و ...) را نرمال می‌کند.
    خروجی:
        (target_type, normalized_value, extra)
        target_type ∈ { "invite", "username", "chat_id" }
    """
    if raw is None:
        return None, None, None

    s = str(raw).strip()
    if not s:
        return None, None, None

    original = s

    # اگر لینک کامل t.me است:
    if s.lower().startswith("http://") or s.lower().startswith("https://"):
        m = re.match(r"^https?://t\.me/(.+)$", s, flags=re.IGNORECASE)
        if m:
            tail = m.group(1)

            # https://t.me/+HASH
            if tail.startswith("+"):
                token = tail[1:].split("?", 1)[0]
                return "invite", f"https://t.me/+{token}", None

            # https://t.me/joinchat/HASH
            if tail.lower().startswith("joinchat/"):
                token = tail.split("/", 1)[1].split("?", 1)[0]
                return "invite", f"https://t.me/joinchat/{token}", None

            # بقیه: می‌تواند یوزرنیم یا آیدی عددی باشد
            token = tail.split("/", 1)[0].split("?", 1)[0]
            token = token.strip("<>\"'")

            if token.startswith("@"):
                token = token[1:]

            if token.lstrip("-").isdigit():
                try:
                    return "chat_id", int(token), None
                except Exception:
                    pass

            return "username", token, None

        # اگر t.me نبود ولی لینک است، برای اسپمر به عنوان invite لحاظ می‌کنیم
        return "invite", original, None

    # این‌جا دیگر http/https نداریم؛ فقط توکن، یوزرنیم یا آیدی عددی است
    s = s.strip("<>\"'")

    # @user
    if s.startswith("@"):
        s = s[1:].strip()

    # +HASH (فرم کوتاه)
    if s.startswith("+"):
        token = s[1:].split("?", 1)[0]
        return "invite", f"https://t.me/+{token}", None

    # آیدی عددی چت
    if s.lstrip("-").isdigit():
        try:
            return "chat_id", int(s), None
        except Exception:
            pass

    # اگر شبیه hash بلند بود، به عنوان invite در نظر می‌گیریم
    token = s.split("/", 1)[-1].split("?", 1)[0]
    token = token.strip()

    if _INVITE_TOKEN_RE.match(token) and len(token) >= 20:
        return "invite", f"https://t.me/+{token}", None

    # در غیر این صورت، به عنوان username
    return "username", token, None


# ============================================================
# 👥 Account List Fetcher
# ============================================================
async def _get_accounts_from_manager(spam_config: Dict[str, Any]) -> List[str]:
    """
    لیست اکانت‌ها را از client_manager یا account_manager می‌گیرد؛
    اگر نشد، از spam_config["accounts"] استفاده می‌کند.
    """
    # 1) client_manager
    if client_manager is not None:
        try:
            if hasattr(client_manager, "get_active_accounts"):
                accs = client_manager.get_active_accounts()
                if asyncio.iscoroutine(accs):
                    accs = await accs
                return list(accs)
        except Exception:
            logger.exception("Failed to get accounts from client_manager; falling back...")

    # 2) account_manager
    if account_manager is not None and hasattr(account_manager, "accounts"):
        try:
            accs = account_manager.accounts()
            if asyncio.iscoroutine(accs):
                accs = await accs
            return list(accs)
        except Exception:
            logger.exception(
                "Failed to get accounts from account_manager; falling back to spam_config['accounts']"
            )

    # 3) config
    return list(spam_config.get("accounts", []))


# ============================================================
# 📊 Stats helper
# ============================================================
def _record_stats(spam_config: Dict[str, Any], acc_phone: str, success: bool) -> None:
    """
    یک رپپر کوچک برای update_stats که اگر target نداشت، یا ارور داد، اسپمر نترکه.
    """
    target = spam_config.get("spamTarget")
    if not target:
        return
    try:
        update_stats(target, acc_phone, success)
    except Exception:
        logger.exception("%s: update_stats failed (success=%s).", acc_phone, success)


# ============================================================
# 📤 Safe Real Send
# ============================================================
async def safe_send_real(
    acc_phone: str,
    spam_config: Dict[str, Any],
    text: str,
    remove_client_from_pool: Callable[[str], None],
) -> bool:
    """
    ارسال واقعی پیام با pyrogram همراه با retry و backoff.
    فقط یک بار برای هر پیام update_stats صدا زده می‌شود:
      - اگر در نهایت موفق شد → success=True
      - اگر همه تلاش‌ها fail شد / خطای جدی → success=False
    """
    # کمی تاخیر تصادفی کوچک برای پخش لود
    await asyncio.sleep(random.uniform(0.05, 0.15))

    if client_manager is None:
        logger.error("client_manager is not available; cannot send messages.")
        # این مورد را جزو fail حساب نمی‌کنیم چون اصلاً تلاشی نشده
        return False

    try:
        cli = await client_manager.get_or_start_client(acc_phone)
        if not cli:
            logger.warning("%s: client unavailable from client_manager.", acc_phone)
            _record_stats(spam_config, acc_phone, False)
            return False
    except Exception as e:
        logger.exception("%s: error while get_or_start_client: %s", acc_phone, e)
        try:
            remove_client_from_pool(acc_phone)
        except Exception:
            pass
        _record_stats(spam_config, acc_phone, False)
        return False

    try:
        target = spam_config.get("spamTarget")
        if not target:
            logger.warning("%s: no spamTarget specified.", acc_phone)
            # target نداشتن را فعلاً در stats لحاظ نمی‌کنیم
            return False

        max_attempts = int(spam_config.get("SEND_RETRY_ATTEMPTS", 3))
        backoff_initial = float(spam_config.get("SEND_BACKOFF_INITIAL", 1.0))
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            try:
                await cli.send_message(target, text)
                logger.info("%s: ✅ Message sent (attempt %d).", acc_phone, attempt)
                _record_stats(spam_config, acc_phone, True)
                return True

            except errors.FloodWait as e:
                delay = backoff_initial * attempt + float(getattr(e, "value", 0))
                logger.warning(
                    "%s: FloodWait %s — sleeping %.1fs (attempt %d/%d).",
                    acc_phone,
                    getattr(e, "value", "?"),
                    delay,
                    attempt,
                    max_attempts,
                )
                await asyncio.sleep(delay)

            except (
                errors.InternalServerError,
                errors.BadGateway,
                errors.RPCError,
            ) as e:
                delay = backoff_initial * attempt
                logger.warning(
                    "%s: transient error %s: %s — retrying in %.1fs.",
                    acc_phone,
                    type(e).__name__,
                    e,
                    delay,
                )
                await asyncio.sleep(delay)

            except errors.AuthKeyUnregistered:
                logger.error("%s: AuthKeyUnregistered — removing from pool.", acc_phone)
                remove_client_from_pool(acc_phone)
                _record_stats(spam_config, acc_phone, False)
                return False

            except errors.UserDeactivated:
                logger.error("%s: UserDeactivated — account disabled.", acc_phone)
                remove_client_from_pool(acc_phone)
                _record_stats(spam_config, acc_phone, False)
                return False

            except errors.ChatWriteForbidden:
                logger.warning("%s: ChatWriteForbidden — cannot send to %s.", acc_phone, target)
                _record_stats(spam_config, acc_phone, False)
                return False

            except Exception as e:
                logger.exception(
                    "%s: unexpected error in send (attempt %d): %s",
                    acc_phone,
                    attempt,
                    e,
                )
                await asyncio.sleep(min(5 * attempt, 30))

        # اگر از حلقه خارج شد یعنی همه‌ی تلاش‌ها ناموفق بوده
        logger.error("%s: ❌ all %d attempts failed.", acc_phone, max_attempts)
        _record_stats(spam_config, acc_phone, False)
        return False

    except Exception as e:
        logger.exception("%s: fatal error in safe_send_real: %s", acc_phone, e)
        remove_client_from_pool(acc_phone)
        _record_stats(spam_config, acc_phone, False)
        return False


# ============================================================
# 🧠 Main Async Runner
# ============================================================
async def run_spammer(
    spam_config: Dict[str, Any],
    remove_client_from_pool: Callable[[str], None],
) -> None:
    """
    حلقه اصلی اسپمر.

    منطق زمان‌بندی جدید (طبق خواسته‌ی تو):
      - delay روی «ست‌ها» (batchها) اعمال می‌شود، نه روی تک‌تک اکانت‌ها.
      - یعنی:
          ست 1  → ۲ ثانیه → ست 2 → ۲ ثانیه → ست 3 → ...
    """
    base_delay = float(spam_config.get("TimeSleep", 2.0))
    batch_size = max(1, int(spam_config.get("BATCH_SIZE", 1)))
    # برای دقت زمانی روی ست‌ها، concurrency = 1 کافی است
    concurrency = 1
    total_ok = 0

    logger.info(
        "Spammer (real) starting: delay_between_batches=%.3fs batch=%d concurrency=%d",
        base_delay,
        batch_size,
        concurrency,
    )

    sem = asyncio.Semaphore(concurrency)

    # برای این‌که اولین ست بدون انتظار انجام شود
    last_batch_start = time.monotonic() - base_delay

    try:
        while spam_config.get("run", False):
            accounts = await _get_accounts_from_manager(spam_config)
            if not accounts:
                logger.warning("No accounts found; sleeping 2s...")
                await asyncio.sleep(2.0)
                continue

            # متن اسپم را فقط یک‌بار برای این راند می‌سازیم
            try:
                text = build_final_text(spam_config)
            except TypeError:
                text = build_final_text()
            except Exception as e:
                logger.warning("build_final_text failed: %s", e)
                text = "[error building text]"

            if not str(text).strip():
                logger.warning("Empty spam text; skipping this round.")
                await asyncio.sleep(base_delay)
                continue

            # پردازش ست‌ها (batchها)
            for i in range(0, len(accounts), batch_size):
                if not spam_config.get("run", False):
                    break

                # ⏱ فاصله‌ی دقیق بین شروع هر ست
                now = time.monotonic()
                elapsed = now - last_batch_start
                if elapsed < base_delay:
                    await asyncio.sleep(base_delay - elapsed)
                last_batch_start = time.monotonic()

                batch = accounts[i: i + batch_size]
                logger.info(
                    "Processing batch %d size=%d (total accounts=%d)",
                    (i // batch_size) + 1,
                    len(batch),
                    len(accounts),
                )

                succ = 0

                for acc in batch:
                    if not spam_config.get("run", False):
                        break

                    logger.info("%s: sending message...", acc)

                    async with sem:
                        ok = await safe_send_real(
                            acc,
                            spam_config,
                            text,
                            remove_client_from_pool,
                        )

                    if ok:
                        succ += 1
                        total_ok += 1

                logger.info(
                    "Batch done: success=%d/%d total_ok=%d",
                    succ,
                    len(batch),
                    total_ok,
                )

    except asyncio.CancelledError:
        logger.info("run_spammer cancelled.")
        raise
    finally:
        logger.info("Spammer (real) stopped. total_ok=%d", total_ok)


# ============================================================
# ⚙️ Wrapper Class + Singleton
# ============================================================
class SpammerThreadingRunner:
    """
    Wrapper ساده که در حلقهٔ async فعلی یک task برای run_spammer ایجاد می‌کند.
    """

    def __init__(self, spam_config: Dict[str, Any], remove_client_from_pool: Callable[[str], None]):
        self.spam_config = spam_config or {}
        self.remove_client_from_pool = remove_client_from_pool
        self._task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError("SpammerThreadingRunner.start must be called from async context.")
        self._loop = loop
        self.spam_config["run"] = True
        self._task = loop.create_task(run_spammer(self.spam_config, self.remove_client_from_pool))
        logger.info("SpammerThreadingRunner started (async task created).")

    def stop(self) -> None:
        logger.info("Stop requested for SpammerThreadingRunner.")
        self.spam_config["run"] = False
        if self._task and not self._task.done():
            self._task.cancel()


_spammer_runner_singleton: Optional[SpammerThreadingRunner] = None


def start_spammer_thread(
    spam_config: Dict[str, Any],
    remove_client_from_pool: Callable[[str], None],
) -> SpammerThreadingRunner:
    global _spammer_runner_singleton
    if (
        _spammer_runner_singleton
        and _spammer_runner_singleton._task
        and not _spammer_runner_singleton._task.done()
    ):
        logger.info("Spammer already running.")
        return _spammer_runner_singleton
    runner = SpammerThreadingRunner(spam_config, remove_client_from_pool)
    runner.start()
    _spammer_runner_singleton = runner
    return runner


def stop_spammer_thread() -> None:
    global _spammer_runner_singleton
    if _spammer_runner_singleton:
        _spammer_runner_singleton.stop()
        _spammer_runner_singleton = None
        logger.info("Spammer stopped (singleton cleared).")
    else:
        logger.info("No running spammer to stop.")
