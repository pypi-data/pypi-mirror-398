
import html
import re
import logging
from typing import List, Tuple, Dict, Any, Iterable,Optional
from ..core.config import spam_config 
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import UsernameNotOccupied
logger = logging.getLogger(__name__)

def _normalize_id_token(tok: str) -> int | None: 
    if tok is None:
        return None
    t = str(tok).strip() 
    if t and (t.lstrip("-").isdigit()):
        try:
            return int(t)
        except Exception:
            return None
    return None


def _add_many_preserve_order(dst: List[int], ids: Iterable[int]) -> Tuple[int, int]: 
    added = 0
    skipped = 0
    exist = set(dst)
    for i in ids:
        try:
            ii = int(i)
        except Exception:
            skipped += 1
            continue
        if ii in exist:
            skipped += 1
            continue
        dst.append(ii)
        exist.add(ii)
        added += 1
    return added, skipped


def _remove_many(dst: List[int], ids: Iterable[int]) -> Tuple[int, int]:
    """
    حذف یک/چند ID از لیست. اگر نبود، شمرده می‌شود به عنوان skipped.
    خروجی: (removed_count, skipped_count)
    """
    removed = 0
    skipped = 0
    s = set(dst)
    for i in ids:
        try:
            ii = int(i)
        except Exception:
            skipped += 1
            continue
        if ii in s: 
            dst[:] = [x for x in dst if x != ii]
            s.discard(ii)
            removed += 1
        else:
            skipped += 1
    return removed, skipped
async def _resolve_one_token_to_id(client: Client, token: str) -> Optional[int]:
    """
    token را به chat/user id عددی تبدیل می‌کند:
      - "me" → id خود اکانت
      - "-100..." یا عدد → همان int
      - "@username" یا "t.me/username" → get_chat → id
    اگر نتوانست، None.
    """
    if token is None:
        return None
    t = token.strip()
    if not t:
        return None

    if t.lower() == "me":
        me = await client.get_me()
        return int(me.id)

    if re.fullmatch(r"-?\d+", t):
        try:
            return int(t)
        except Exception:
            return None

    username = t
    if username.startswith("@"):
        username = username[1:]
    if "t.me/" in username.lower():
        username = re.sub(r"^https?://t\.me/", "", username, flags=re.IGNORECASE).strip("/")

    try:
        ch = await client.get_chat(username)
        return int(ch.id)
    except (UsernameNotOccupied, Exception):
        return None


async def _resolve_many_tokens_to_ids(client: Client, tokens: List[str]) -> List[int]:
    """لیست توکن‌ها را به لیست ID عددی تبدیل می‌کند (تبدیل‌های ناموفق حذف می‌شوند)."""
    out: List[int] = []
    for tok in tokens:
        cid = await _resolve_one_token_to_id(client, tok)
        if cid is not None:
            out.append(cid)
    return out
async def set_mention_text(text: str) -> str:
    if not (text or "").strip():
        return "❌ متن منشن نمی‌تواند خالی باشد."
    spam_config["textMen"] = text.strip()
    logger.info(f"✅ Mention text set: {text.strip()}")
    return "✅ متن منشن تنظیم شد."

async def set_mention_user(user_id: int) -> str:
    try:
        uid = int(user_id)
    except Exception:
        return "❌ شناسه کاربر معتبر نیست."
    spam_config["useridMen"] = uid
    logger.info(f"✅ Mention target set: {uid}")
    return f"✅ کاربر {uid} برای منشن تنظیم شد."

async def toggle_mention(enable: bool) -> str:
    spam_config["is_menshen"] = bool(enable)
    logger.info(f"🔄 Single mention {'enabled' if enable else 'disabled'}.")
    return "✅ منشن تکی فعال شد." if enable else "🛑 منشن تکی غیرفعال شد."


async def toggle_group_mention(enable: bool) -> str:
    spam_config["group_menshen"] = bool(enable)
    logger.info(f"🔄 Group mention {'enabled' if enable else 'disabled'}.")
    return "✅ منشن گروهی فعال شد." if enable else "🛑 منشن گروهی غیرفعال شد."


async def add_groups_by_ids(*ids: int | str) -> str:
    groups: List[int] = spam_config["group_ids"]

    norm = []
    for t in ids:
        n = _normalize_id_token(str(t))
        if n is not None:
            norm.append(n)

    if not norm:
        return "❌ هیچ شناسهٔ معتبری دریافت نشد."

    added, skipped = _add_many_preserve_order(groups, norm)
    logger.info(f"✅ Group IDs added: +{added} / skipped:{skipped} → total:{len(groups)}")
    if added and not spam_config.get("group_menshen", False):
        return f"✅ {added} شناسه افزوده شد. ℹ️ برای استفاده، منشن گروهی را فعال کنید."
    return f"✅ {added} شناسه افزوده شد. {'(برخی تکراری/نامعتبر بودند.)' if skipped else ''}".strip()

async def add_group_from_reply(user_id: int) -> str:
    try:
        uid = int(user_id)
    except Exception:
        return "❌ شناسهٔ ریپلای معتبر نیست."

    groups: List[int] = spam_config["group_ids"]
    added, skipped = _add_many_preserve_order(groups, [uid])
    logger.info(f"✅ Group add from reply: +{added} (uid={uid}) → total:{len(groups)}")
    return "✅ شناسهٔ کاربرِ ریپلای به لیست منشن گروهی اضافه شد." if added else "ℹ️ این شناسه قبلاً در لیست بود."


async def remove_groups_by_ids(*ids: int | str) -> str:
    groups: List[int] = spam_config["group_ids"]

    norm = []
    for t in ids:
        n = _normalize_id_token(str(t))
        if n is not None:
            norm.append(n)

    if not norm:
        return "❌ هیچ شناسهٔ معتبری برای حذف دریافت نشد."

    removed, skipped = _remove_many(groups, norm)
    logger.info(f"🗑️ Group IDs removed: -{removed} / skipped:{skipped} → total:{len(groups)}")
    if removed:
        if skipped:
            return f"🗑️ {removed} شناسه حذف شد. (برخی یافت نشدند.)"
        return f"🗑️ {removed} شناسه حذف شد."
    return "ℹ️ هیچ‌کدام از شناسه‌ها در لیست نبود."

async def clear_groups() -> str:
    spam_config["group_ids"] = []
    logger.info("🧹 All group mention IDs cleared.")
    return "🧹 تمام گروه‌های منشن پاک شدند."

async def mention_status() -> str: 
    text = spam_config["textMen"]
    user_id = spam_config["useridMen"]
    single_enabled = bool(spam_config["is_menshen"])
    group_enabled = bool(spam_config["group_menshen"])
    groups = list(spam_config["group_ids"])

    msg = (
        "📋 **وضعیت منشن:**\n"
        f"💬 متن منشن: {text or '—'}\n"
        f"🎯 کاربر تکی: `{user_id or '—'}` — {'✅' if single_enabled else '❌'}\n"
        f"👥 گروهی فعال: {'✅' if group_enabled else '❌'}\n"
        f"📦 تعداد شناسه‌های گروهی: {len(groups)}\n"
    )

    if groups:
        msg += "\n🗂 **لیست گروهی (به ترتیب):**\n"
        msg += "\n".join([f"{i+1}. `{gid}`" for i, gid in enumerate(groups)])

    logger.info("📊 Mention status displayed.")
    return msg

def make_mention_html(user_id: int, text: str) -> str:
    """ساخت منشن HTML تلگرام به یک کاربر."""
    return f'<a href="tg://user?id={int(user_id)}">{html.escape(text or str(user_id))}</a>'
