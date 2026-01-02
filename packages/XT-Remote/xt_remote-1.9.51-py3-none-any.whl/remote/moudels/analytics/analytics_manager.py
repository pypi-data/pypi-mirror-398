# remote/moudels/analytics_manager.py
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

# ============================================================
# 📦 تنظیمات اولیه
# ============================================================

logger = logging.getLogger("remote.moudels.analytics")
logger.setLevel(logging.INFO)

AN_DIR = os.path.join("logs", "analytics")
os.makedirs(AN_DIR, exist_ok=True)


# ============================================================
# ⏱ زمان
# ============================================================

def _now_iso() -> str:
    """زمان فعلی به صورت ISO برای ذخیره در JSON."""
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


# ============================================================
# 🧹 تمیز کردن target و نام فایل
# ============================================================

def _sanitize_target(raw_target: Any) -> Tuple[str, str]:
    """
    ورودی target (مثلاً لینک/یوزرنیم/آیدی) را به دو چیز تبدیل می‌کند:
      - display_name: برای نمایش در /stats
      - stats_name: برای نام فایل (safe)

    خروجی: (display_name, stats_name)
    """
    if raw_target is None:
        return "unknown", "default"

    s = str(raw_target).strip()
    if not s:
        return "unknown", "default"

    display_name = s

    # اگر لینک t.me هست، یک مقدار تمیز تر برای نمایش در نظر می‌گیریم
    # مثلاً:
    #   https://t.me/+AbCdEf -> +AbCdEf
    #   https://t.me/joinchat/AbCdEf -> joinchat/AbCdEf
    #   https://t.me/MyGroup -> MyGroup
    if s.lower().startswith("http://") or s.lower().startswith("https://"):
        m = re.match(r"^https?://t\.me/(.+)$", s, flags=re.IGNORECASE)
        if m:
            tail = m.group(1)
            display_name = tail.split("?", 1)[0]
        else:
            # لینک غیر t.me
            display_name = s

    # برای stats_name باید چیزی امن برای نام فایل بسازیم
    base = display_name
    base = base.strip("<>\"' ")

    # فقط حروف، اعداد، نقطه، خط‌تیره و زیرخط نگه می‌داریم
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", base).strip("_")
    if not safe:
        safe = "default"

    return display_name, safe


def _stats_path(name: str) -> str:
    """
    بر اساس نام stats_name یک مسیر امن روی دیسک می‌سازد.
    مثال:
      name="MyGroup" -> logs/analytics/MyGroup.json
    """
    if not name:
        name = "default"

    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(name)).strip("_")
    if not safe:
        safe = "default"

    return os.path.join(AN_DIR, f"{safe}.json")


# ============================================================
# 📄 کمکی برای خواندن/نوشتن JSON
# ============================================================

def _load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Failed to load stats json %s: %s", path, e)
        return {}


def _save_json(path: str, data: Dict[str, Any]) -> None:
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception as e:
        logger.error("Failed to save stats json %s: %s", path, e)


# ============================================================
# 🔢 هسته‌ی آمار: update / get
# ============================================================

def update_stats(target: Any, acc_phone: str, success: bool) -> None:
    """
    آپدیت کردن آمار برای یک target خاص و یک اکانت خاص.

    پارامترها:
      - target: همون spamTarget که توی spam_config هست (لینک/یوزرنیم/آیدی)
      - acc_phone: شماره اکانتی که پیام را ارسال کرده
      - success: اگر True یعنی ارسال موفق، اگر False یعنی fail

    ساختار ذخیره در JSON:
    {
      "target": "MyGroup",
      "stats_name": "MyGroup",
      "created_at": "...",
      "updated_at": "...",
      "total": 10,
      "success": 8,
      "fail": 2,
      "accounts": {
        "+9899450...": { "total": 6, "success": 5, "fail": 1 },
        "+9890137...": { "total": 4, "success": 3, "fail": 1 }
      }
    }
    """
    display_name, stats_name = _sanitize_target(target)
    path = _stats_path(stats_name)

    data = _load_json(path)
    now = _now_iso()

    if not data:
        data = {
            "target": display_name,
            "stats_name": stats_name,
            "created_at": now,
            "updated_at": now,
            "total": 0,
            "success": 0,
            "fail": 0,
            "accounts": {},
        }

    data["target"] = display_name
    data["stats_name"] = stats_name
    data["updated_at"] = now

    # کل
    data["total"] = int(data.get("total", 0)) + 1
    if success:
        data["success"] = int(data.get("success", 0)) + 1
    else:
        data["fail"] = int(data.get("fail", 0)) + 1

    # per-account
    acc_key = str(acc_phone)
    acc_info = data.setdefault("accounts", {}).get(acc_key) or {
        "total": 0,
        "success": 0,
        "fail": 0,
        "created_at": now,
        "updated_at": now,
    }

    acc_info["total"] = int(acc_info.get("total", 0)) + 1
    if success:
        acc_info["success"] = int(acc_info.get("success", 0)) + 1
    else:
        acc_info["fail"] = int(acc_info.get("fail", 0)) + 1
    acc_info["updated_at"] = now

    data["accounts"][acc_key] = acc_info

    _save_json(path, data)


def get_stats(target: Any) -> Dict[str, Any]:
    """
    استیت مربوط به یک target مشخص را می‌خواند.
    اگر فایل وجود نداشت، یک دیکشنری خالی برمی‌گرداند.
    """
    _display, stats_name = _sanitize_target(target)
    path = _stats_path(stats_name)
    return _load_json(path)


def get_all_stats() -> List[Dict[str, Any]]:
    """
    تمام فایل‌های داخل logs/analytics را لود می‌کند و
    لیستی از دیکشنری‌های stats برمی‌گرداند.
    """
    results: List[Dict[str, Any]] = []

    if not os.path.isdir(AN_DIR):
        return results

    for fname in os.listdir(AN_DIR):
        if not fname.lower().endswith(".json"):
            continue
        path = os.path.join(AN_DIR, fname)
        data = _load_json(path)
        if data:
            results.append(data)

    # مرتب‌سازی بر اساس updated_at (جدیدترین بالا)
    def _sort_key(d: Dict[str, Any]) -> str:
        return str(d.get("updated_at", ""))

    results.sort(key=_sort_key, reverse=True)
    return results


# ============================================================
# 🧾 فرمت برای نمایش در CLI
# ============================================================

def _ratio(num: int, den: int) -> str:
    if den <= 0:
        return "0.0%"
    return f"{(num / den) * 100:.1f}%"


def format_stats_dict(data: Dict[str, Any]) -> str:
    """
    یک دیکشنری stats را به متن مرتب برای نمایش تبدیل می‌کند.
    """
    if not data:
        return "هیچ آماری یافت نشد."

    target = data.get("target", data.get("stats_name", "unknown"))
    total = int(data.get("total", 0))
    success = int(data.get("success", 0))
    fail = int(data.get("fail", 0))
    created_at = data.get("created_at", "?")
    updated_at = data.get("updated_at", "?")

    lines: List[str] = []
    lines.append(f"🎯 Target: {target}")
    lines.append(f"📝 Created: {created_at}")
    lines.append(f"🔁 Updated: {updated_at}")
    lines.append("")
    lines.append(f"📊 Total: {total}")
    lines.append(f"✅ Success: {success} ({_ratio(success, total)})")
    lines.append(f"❌ Fail:   {fail} ({_ratio(fail, total)})")

    accounts = data.get("accounts") or {}
    if accounts:
        lines.append("")
        lines.append("👥 Per-account:")
        # sort by total desc
        sorted_items = sorted(
            accounts.items(),
            key=lambda kv: int(kv[1].get("total", 0)),
            reverse=True,
        )
        for acc, info in sorted_items:
            atotal = int(info.get("total", 0))
            asucc = int(info.get("success", 0))
            afail = int(info.get("fail", 0))
            lines.append(
                f"  • {acc}: total={atotal}, "
                f"success={asucc} ({_ratio(asucc, atotal)}), "
                f"fail={afail} ({_ratio(afail, atotal)})"
            )

    return "\n".join(lines)


def format_stats_for_target(target: Any) -> str:
    """
    برای یک target خاص، متن آماده‌ی نمایش می‌سازد.
    """
    data = get_stats(target)
    if not data:
        display, _ = _sanitize_target(target)
        return f"برای target «{display}» هنوز آماری ثبت نشده است."
    return format_stats_dict(data)


def format_all_stats() -> str:
    """
    همه‌ی target ها را در یک متن زیر هم برمی‌گرداند.
    مناسب برای /stats بدون آرگومان.
    """
    all_data = get_all_stats()
    if not all_data:
        return "هنوز هیچ آماری ثبت نشده است."

    parts: List[str] = []
    for i, d in enumerate(all_data, start=1):
        parts.append(f"===== [{i}] =====")
        parts.append(format_stats_dict(d))
        parts.append("")

    return "\n".join(parts).strip()


# ============================================================
# ✅ تست سریع (اختیاری)
# ============================================================
if __name__ == "__main__":
    # تست خیلی ساده‌ی local
    update_stats("https://t.me/MyTestGroup", "+989945051172", True)
    update_stats("https://t.me/MyTestGroup", "+989945051172", False)
    update_stats("https://t.me/MyTestGroup", "+989013728416", True)

    print(format_stats_for_target("https://t.me/MyTestGroup"))
    print("\n------------------\n")
    print(format_all_stats())
