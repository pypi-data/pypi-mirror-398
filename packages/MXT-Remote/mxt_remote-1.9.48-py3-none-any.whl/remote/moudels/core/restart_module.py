import os
import logging
from typing import List, Set, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

root_logger = logging.getLogger()

BASE_DIR = Path(__file__).resolve().parent
# اگر می‌خواهید همچنان یک سری فایل مشخص را هم خالی نگه دارید:
EXTRA_TARGET_LOG_FILES: List[Path] = [
    BASE_DIR / "logs" / "spam_log.txt",
    BASE_DIR / "logs" / "client_debug_log.txt",
    BASE_DIR / "logs" / "admins_log.txt",
    BASE_DIR / "logs" / "analytics_log.txt",
    BASE_DIR / "logs" / "sqlite_health.log",
    BASE_DIR / "logs" / "clean_acc.txt",   
]

def _collect_file_handlers() -> List[logging.FileHandler]:
    """تمام FileHandler های همه‌ی لاگرها را برمی‌گرداند (شامل روت)."""
    handlers: List[logging.FileHandler] = []
    # همه لاگرهای شناخته‌شده:
    all_loggers = {root_logger, logger}
    # همچنین از درخت لاگرها استفاده کنیم (در صورت ثبت‌شدن):
    all_loggers.update(
        lg for lg_name, lg in logging.Logger.manager.loggerDict.items()
        if isinstance(lg, logging.Logger)
    )
    for lg in all_loggers:
        for h in getattr(lg, "handlers", []):
            if isinstance(h, logging.FileHandler):
                handlers.append(h)
    return handlers

def _handler_paths(handlers: List[logging.FileHandler]) -> Set[Path]:
    """مسیر مطلق فایل هر FileHandler را استخراج می‌کند."""
    paths: Set[Path] = set()
    for h in handlers:
        try:
            # baseFilename همیشه مطلق است
            p = Path(h.baseFilename).resolve()
            paths.add(p)
        except Exception:
            pass
    return paths

def _truncate_handler_stream(h: logging.FileHandler) -> bool:
    """محتوای فایل هندلر را از طریق همان stream خالی می‌کند."""
    try:
        h.acquire()
        try:
            h.flush()
            if getattr(h, "stream", None):
                h.stream.seek(0)
                h.stream.truncate(0)
            return True
        finally:
            h.release()
    except Exception as e:
        logger.error(f"⚠️ Error truncating handler stream for {getattr(h, 'baseFilename', '?')}: {e}")
        return False

def _truncate_path(path: Path) -> bool:
    """اگر فایل هست، خالی‌اش می‌کند؛ اگر نیست، می‌سازد و خالی می‌گذارد."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.truncate(0)
        return True
    except Exception as e:
        logger.error(f"⚠️ Error truncating {path}: {e}")
        return False

def clear_logs() -> int:
    """
    همه فایل‌هایی که FileHandler لاگرها به آن‌ها وصل‌اند را *درجا* خالی می‌کند.
    همچنین فایل‌های EXTRA_TARGET_LOG_FILES را نیز خالی نگه می‌دارد.
    خروجی: تعداد فایل‌هایی که واقعاً خالی شدند.
    """
    handlers = _collect_file_handlers()

    # 1) فایل‌های متصل به لاگرها (مسیرهای واقعی)
    handler_files = _handler_paths(handlers)

    cleared = 0

    # 1-a) truncate از طریق خودِ stream هندلر (سازگار با ویندوز)
    for h in handlers:
        ok = _truncate_handler_stream(h)
        if ok:
            cleared += 1
            # از همین logger ننویسیم که دوباره چیزی به فایل اضافه شود؛ اگر می‌خواهید:
            # logger.info(f"🧹 Cleared (via handler) → {h.baseFilename}")

    # 2) فایل‌های اضافه‌ای که ممکنه handler نداشته باشند ولی می‌خواهید خالی باشند
    for p in EXTRA_TARGET_LOG_FILES:
        # اگر همین فایل قبلاً از طریق هندلر خالی شده، دوباره لازم نیست
        if p.resolve() in handler_files:
            continue
        if _truncate_path(p):
            cleared += 1
            # logger.info(f"🧹 Cleared (extra) → {p}")

    return cleared

# اختیاری: ابزار تشخیصی برای اطمینان از اینکه دارید فایل درست را می‌زنید
def debug_list_active_log_files() -> List[Tuple[str, int]]:
    """
    لیست مسیرهای واقعی فایل‌های متصل به FileHandlerها + سایز فعلی‌شان.
    """
    out = []
    for p in _handler_paths(_collect_file_handlers()):
        try:
            size = p.stat().st_size
        except FileNotFoundError:
            size = -1
        out.append((str(p), size))
    return out
