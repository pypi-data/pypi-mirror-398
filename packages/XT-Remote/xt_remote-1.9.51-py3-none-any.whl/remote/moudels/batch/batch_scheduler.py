import asyncio
import logging
from typing import List, Callable, Any

logger = logging.getLogger(__name__)

# ============================================================
# ⚙️ BatchScheduler — زمان‌بندی بدون افت سرعت
# ============================================================
class BatchScheduler:
    """
    زمان‌بند هوشمند برای اجرای batchهای async بدون drift.
    ویژگی‌ها:
      ✅ drift-free (بر اساس loop.time)
      ✅ سرعت ثابت حتی در BATCH_SIZE بالا
      ✅ کنترل دقیق زمان شروع batchها
      ✅ بدون delay اضافی یا قفل ناخواسته
    """

    def __init__(
        self,
        base_delay: float = 2.0,
        batch_size: int = 2,
        on_batch_start: Callable[[int, List[str]], Any] | None = None,
    ):
        self.base_delay = max(0.1, float(base_delay))
        self.batch_size = max(1, int(batch_size))
        self.on_batch_start = on_batch_start

        self._loop = asyncio.get_event_loop()
        self._next_batch_start = None
        self._batch_index = 0

    # ============================================================
    # 🚀 اجرای Batchها با کنترل دقیق زمان و سرعت بالا
    # ============================================================
    async def schedule_batches(
        self,
        accounts: List[str],
        send_task: Callable[[str], Any],
    ) -> int:
        """
        اجرای ارسال‌ها در batchهای دقیق و بدون drift.
        هر batch شامل N اکانت بوده و به‌صورت async هم‌زمان اجرا می‌شود.
        """
        if not accounts:
            logger.debug("⚠️ No active accounts for scheduling.")
            return 0

        # آماده‌سازی batchها
        batches = [accounts[i:i + self.batch_size]
                   for i in range(0, len(accounts), self.batch_size)]
        total_sent = 0

        # تنظیم مرجع زمان برای batch اول
        if self._next_batch_start is None:
            self._next_batch_start = self._loop.time()

        for batch in batches:
            self._batch_index += 1

            # انتظار دقیق تا لحظه‌ی هدف batch بعدی
            now = self._loop.time()
            wait_time = self._next_batch_start - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            batch_real_start = self._loop.time()
            drift = batch_real_start - self._next_batch_start

            if self.on_batch_start:
                try:
                    self.on_batch_start(self._batch_index, batch)
                except Exception as e:
                    logger.warning(f"⚠️ on_batch_start callback failed: {e}")

            logger.debug(
                f"⏱️ Batch {self._batch_index:03d} | "
                f"Accounts={len(batch)} | Drift={drift:+.6f}s"
            )

            # اجرای موازی سریع و سبک
            try:
                results = await asyncio.gather(
                    *[send_task(acc) for acc in batch],
                    return_exceptions=True,
                )
            except Exception as e:
                logger.warning(f"⚠️ Batch {self._batch_index} execution error: {e}")
                results = []

            # شمارش موفقیت‌ها
            batch_sent = sum(1 for r in results if r is True)
            total_sent += batch_sent

            # محاسبه زمان batch بعدی (drift-free)
            self._next_batch_start = batch_real_start + self.base_delay

        return total_sent

    # ============================================================
    # 🔁 بازنشانی زمان‌بند (در توقف موقت)
    # ============================================================
    def reset(self):
        """بازنشانی شمارنده‌ها و زمان برای شروع مجدد"""
        self._batch_index = 0
        self._next_batch_start = None
