 
import random
import re
from typing import List, Optional, Union
from .text_manager import get_spam_texts
from ..core.config import spam_config
from .mention_manager import make_mention_html   
try: 
    from pyrogram.types import Message as _PyroMessage  
except Exception:
    _PyroMessage = None  


def get_random_text() -> str:
    try:
        txt = get_spam_texts()
        if not txt or not str(txt).strip():
            raise ValueError("Empty spam text list.")
        return str(txt).strip()
    except Exception:
        return "Default test message from get_random_text()"

def _caption_from_config() -> str:
    caption = spam_config["caption"]
    return f"\n{caption}"

_USERNAME_RE = re.compile(r"[A-Za-z0-9_]{3,}")

def _normalize_user_id(val) -> Optional[int]:
    """اگر ورودی عددی باشد به int برمی‌گرداند، وگرنه None."""
    try:
        s = str(val).strip().lstrip("@")
        return int(s)
    except Exception:
        return None

def _normalize_username(val) -> Optional[str]:
    """اگر ورودی username معتبر باشد (با/بی‌@)، برمی‌گرداند؛ وگرنه None."""
    try:
        s = str(val).strip().lstrip("@")
        if not s:
            return None
        return s if _USERNAME_RE.fullmatch(s) else None
    except Exception:
        return None

def _make_username_link_html(username: str, label_text: str) -> str:
    visible = (label_text or "").strip() or f"@{username}"
    return f'<a href="https://t.me/{username}">{visible}</a>'


def build_mentions() -> str:
    parts: List[str] = []

    label_cfg = spam_config["textMen"].strip()
    default_label = label_cfg or "mention"

    single_val = spam_config["useridMen"]
    if spam_config["is_menshen"] and single_val:
        uid = _normalize_user_id(single_val)
        if uid is not None:
            parts.append(make_mention_html(uid, default_label))
        else:
            uname = _normalize_username(single_val)
            if uname:
                parts.append(_make_username_link_html(uname, label_cfg))

    if spam_config["group_menshen"] and spam_config["group_ids"]:
        for gid in spam_config["group_ids"]:
            uid = _normalize_user_id(gid)
            if uid is not None:
                parts.append(make_mention_html(uid, default_label))
            else:
                uname = _normalize_username(gid)
                if uname:
                    parts.append(_make_username_link_html(uname, label_cfg))

    return ("\n" + " ".join(parts)) if parts else ""


def _extract_from_message(msg) -> tuple[str, str]:
    base_text = ""
    msg_caption = ""
    try:
        cap = (getattr(msg, "caption", None) or "").strip()
        txt = (getattr(msg, "text", None) or "").strip()
        base_text = cap or txt or ""
        msg_caption = ""
    except Exception:
        pass
    return base_text, msg_caption


def build_final_text(base: Optional[Union[str, object]] = None) -> str:
    msg_given = (_PyroMessage is not None and isinstance(base, _PyroMessage))

    if msg_given:
        base_text, msg_caption = _extract_from_message(base)
        caption_part = msg_caption 
    else:
        base_text = (str(base).strip() if isinstance(base, str) else "") or get_random_text()
        caption_part = _caption_from_config()

    if not base_text:
        return ""

    mentions_part = build_mentions()
    return "".join([base_text, caption_part, mentions_part])
