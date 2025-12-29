# antispam_core/precise_engine.py
import asyncio
import time

class PreciseTicker:
    """
    تیکر دقیق برای فاصله‌های زمانی ثابت بدون drift.
    این کلاس تضمین می‌کند که هر sleep دقیقاً در فواصل ثابت نسبت به زمان شروع اتفاق بیفتد،
    حتی اگر coroutine‌های دیگر کمی تأخیر ایجاد کنند.
    """

    def __init__(self, interval: float):
        self.interval = float(interval)
        self.loop = asyncio.get_event_loop()
        self.next_tick = self.loop.time()

    async def sleep(self):
        """
        خواب دقیق بدون انباشته شدن تاخیر (drift-free)
        """
        self.next_tick += self.interval
        delay = self.next_tick - self.loop.time()

        # اگر زمان تا تیک بعدی مثبت است، به همان اندازه بخواب
        if delay > 0:
            await asyncio.sleep(delay)
        else:
            # اگر از زمان هدف گذشت، برای جلوگیری از انباشته شدن تاخیر، 
            # زمان مرجع را به حال حاضر تنظیم می‌کنیم.
            self.next_tick = self.loop.time()

    def reset(self):
        """بازنشانی تیکر"""
        self.next_tick = self.loop.time()

