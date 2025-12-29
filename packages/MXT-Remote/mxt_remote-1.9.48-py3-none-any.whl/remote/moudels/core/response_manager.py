import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Union, Callable
from pyrogram import Client, types

# ============================================================
# ⚙️ Logger setup
# ============================================================
logger = logging.getLogger("ResponseManagerAIInfinity")
logger.setLevel(logging.INFO)
if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
    fh = logging.FileHandler("logs/response_manager_ai_infinity.log", encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

# ============================================================
# 🎨 Styles and Icons
# ============================================================
STYLE = {
    "info": "💬",
    "success": "✅",
    "error": "❌",
    "warn": "⚠️",
    "progress": "⏳",
    "done": "🎯",
    "spark": "✨",
    "rocket": "🚀",
    "clean": "🧹",
    "typing": "✍️",
    "ai": "🤖",
    "voice": "🎙️",
}

# ============================================================
# 🧠 ResponseManagerAIInfinity
# ============================================================
class ResponseManagerAIInfinity:
    """
    🧠 ResponseManagerAIInfinity
    نسخه نهایی سیستم هوشمند مدیریت پاسخ برای Pyrogram.
    """

    def __init__(self, client: Client, admin_id: Optional[int] = None):
        self.client = client
        self.admin_id = admin_id
        self.temp_messages: List[types.Message] = []
        self.hooks: Dict[str, List[Callable]] = {
            "before_send": [],
            "after_send": [],
            "before_delete": [],
            "after_delete": [],
        }

    # ============================================================
    # 🧩 Hook Management
    # ============================================================
    def on(self, event: str):
        """Decorator for hooks: before_send, after_send, etc."""
        def decorator(func):
            if event in self.hooks:
                self.hooks[event].append(func)
            return func
        return decorator

    async def _trigger(self, event: str, *args, **kwargs):
        if event in self.hooks:
            for func in self.hooks[event]:
                try:
                    await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Hook error in {event}: {e}")

    # ============================================================
    # 💬 Smart Send
    # ============================================================
    async def smart_send(
        self,
        message: types.Message,
        content: Union[str, dict],
        caption: Optional[str] = None,
        mode: str = "info",
        reply: bool = True,
        **kwargs,
    ):
        """ارسال خودکار با تشخیص نوع پیام و ایموجی استایل‌دار"""
        await self._trigger("before_send", message, content)
        emoji = STYLE.get(mode, STYLE["info"])
        msg = None
        try:
            chat_id = message.chat.id
            if isinstance(content, str):
                msg = await (message.reply_text if reply else self.client.send_message)(chat_id, f"{emoji} {content}", **kwargs)
            elif isinstance(content, dict):
                t = content.get("type")
                d = content.get("data")
                if t == "photo":
                    msg = await self.client.send_photo(chat_id, d, caption=caption or "")
                elif t == "video":
                    msg = await self.client.send_video(chat_id, d, caption=caption or "")
                elif t == "document":
                    msg = await self.client.send_document(chat_id, d, caption=caption or "")
                elif t == "voice":
                    msg = await self.client.send_voice(chat_id, d, caption=caption or "")
                elif t == "animation":
                    msg = await self.client.send_animation(chat_id, d, caption=caption or "")
                elif t == "sticker":
                    msg = await self.client.send_sticker(chat_id, d)
                else:
                    msg = await message.reply_text(f"⚠️ نوع داده پشتیبانی نمی‌شود: {t}")
            await self._trigger("after_send", msg)
            return msg
        except Exception as e:
            logger.error(f"smart_send error: {e}")
            return await message.reply_text(f"❌ خطا در ارسال: {e}")

    # ============================================================
    # ⏳ Temporary Message
    # ============================================================
    async def temp_message(self, message: types.Message, text="⏳ لطفاً صبر کنید...", delay: float = 3.0, auto_delete: bool = True):
        msg = await message.reply_text(text)
        self.temp_messages.append(msg)
        await asyncio.sleep(delay)
        if auto_delete:
            await self.safe_delete(msg)
        return msg

    # ============================================================
    # ✍️ Typing Animation
    # ============================================================
    async def typing_animation(
        self, message: types.Message, texts: List[str], delay: float = 0.5, final_text: Optional[str] = None, emoji: str = "✍️"
    ):
        msg = await message.reply_text(f"{emoji} {texts[0]}")
        for t in texts[1:]:
            await asyncio.sleep(delay)
            await msg.edit_text(f"{emoji} {t}")
        if final_text:
            await asyncio.sleep(delay)
            await msg.edit_text(f"{STYLE['success']} {final_text}")
        return msg

    # ============================================================
    # 🌀 Progress Bar
    # ============================================================
    async def progress_bar(
        self,
        message: types.Message,
        title="در حال انجام...",
        steps: int = 10,
        delay: float = 0.3,
        style: str = "spark",
    ):
        msg = await message.reply_text(f"{STYLE['progress']} {title} [0%]")
        for i in range(1, steps + 1):
            percent = int((i / steps) * 100)
            bar = "▓" * (i // 2) + "░" * ((steps - i) // 2)
            await asyncio.sleep(delay)
            await msg.edit_text(f"{STYLE[style]} {title}\n[{bar}] {percent}%")
        await msg.edit_text(f"{STYLE['done']} {title} تکمیل شد!")
        return msg

    # ============================================================
    # 🔁 Dynamic Edit
    # ============================================================
    async def dynamic_update(self, msg: types.Message, updates: List[str], delay: float = 0.8):
        for text in updates:
            await asyncio.sleep(delay)
            await msg.edit_text(text)

    # ============================================================
    # ❌ Safe Delete
    # ============================================================
    async def safe_delete(self, msg: Optional[types.Message], delay: float = 0.0):
        if not msg:
            return
        await self._trigger("before_delete", msg)
        if delay:
            await asyncio.sleep(delay)
        try:
            await msg.delete()
        except Exception:
            pass
        await self._trigger("after_delete", msg)

    # ============================================================
    # 🧩 Chain Operations
    # ============================================================
    async def chain_actions(self, message: types.Message, steps: List[str], delay: float = 1.0):
        msg = await message.reply_text(steps[0])
        for step in steps[1:]:
            await asyncio.sleep(delay)
            await msg.edit_text(step)
        return msg

    # ============================================================
    # 🎭 Styled Reaction
    # ============================================================
    async def styled_react(self, message: types.Message, text: str, style: str = "info", delete_after: Optional[float] = None):
        emoji = STYLE.get(style, STYLE["info"])
        msg = await message.reply_text(f"{emoji} {text}")
        if delete_after:
            await asyncio.sleep(delete_after)
            await self.safe_delete(msg)
        return msg

    # ============================================================
    # 📦 Batch Send
    # ============================================================
    async def batch_send(self, chat_id: int, messages: List[str], delay: float = 0.7, as_edit=False):
        msg = None
        for m in messages:
            if as_edit and msg:
                await msg.edit_text(m)
            else:
                msg = await self.client.send_message(chat_id, m)
            await asyncio.sleep(delay)
        return msg

    # ============================================================
    # 🎙️ Voice Typing Simulation
    # ============================================================
    async def voice_typing(self, message: types.Message, duration: int = 5):
        """نمایش افکت ضبط صدا"""
        msg = await message.reply_text("🎙️ در حال ضبط صدا...")
        for i in range(duration):
            dots = "." * ((i % 3) + 1)
            await asyncio.sleep(1)
            await msg.edit_text(f"🎙️ در حال ضبط{dots}")
        await msg.edit_text("✅ ضبط کامل شد.")
        return msg

    # ============================================================
    # 🧠 Context-Aware Response
    # ============================================================
    async def context_response(self, message: types.Message):
        """پاسخ خودکار بر اساس نوع ورودی"""
        if message.photo:
            return await self.styled_react(message, "📸 عکس دریافت شد.", "info")
        elif message.video:
            return await self.styled_react(message, "🎥 ویدیو دریافت شد.", "info")
        elif message.document:
            return await self.styled_react(message, "📄 فایل دریافت شد.", "info")
        elif message.voice:
            return await self.styled_react(message, "🎙️ ویس دریافت شد.", "info")
        elif message.text:
            if message.text.startswith("/"):
                return await self.styled_react(message, "⚙️ دستور شناسایی شد.", "info")
            else:
                return await self.styled_react(message, "💬 پیام متنی دریافت شد.", "info")
        return await self.styled_react(message, "❔ نوع پیام نامشخص.", "warn")

    # ============================================================
    # 🔔 Admin Notify
    # ============================================================
    async def notify_admin(self, text: str):
        if not self.admin_id:
            return
        try:
            await self.client.send_message(self.admin_id, f"🔔 اعلان سیستم:\n{text}")
        except Exception as e:
            logger.error(f"notify_admin error: {e}")

    # ============================================================
    # 🧵 Context Manager
    # ============================================================
    async def __aenter__(self):
        self.start_time = datetime.now()
        logger.info("ResponseManagerAIInfinity context started")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        for msg in self.temp_messages:
            await self.safe_delete(msg)
        logger.info("ResponseManagerAIInfinity context ended")
