"""
Bot sozlamalarini boshqarish va saqlash moduli.
Admin tomonidan kiritilgan sozlamalarni doimiy (persistent) saqlaydi.
"""
import json
import logging
import os
import re
import threading
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_settings.json')
_lock = threading.Lock()

DEFAULT_SETTINGS = {
    "work_start_time": "05:00",
    "report_offset_minutes": 15
}


def load_settings() -> dict:
    with _lock:
        if not os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(DEFAULT_SETTINGS, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Sozlamalar faylini yaratishda xato: {e}")
            return DEFAULT_SETTINGS.copy()

        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Standart qiymatlarni to'ldirish
                for k, v in DEFAULT_SETTINGS.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception as e:
            logger.error(f"Sozlamalar faylini o'qishda xato: {e}")
            return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> bool:
    with _lock:
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Sozlamalar faylini saqlashda xato: {e}")
            return False


def parse_time_str(time_str: str) -> Optional[Tuple[int, int]]:
    """'05:00' yoki '5:30' ko'rinishidagi vaqtni (hour, minute) ga aylantiradi"""
    if not time_str:
        return None
    match = re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", time_str.strip())
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def get_work_start_time() -> Tuple[int, int]:
    """Ertalabki ish boshlash vaqti (soat, daqiqa)"""
    settings = load_settings()
    time_str = settings.get("work_start_time", "05:00")
    parsed = parse_time_str(time_str)
    return parsed if parsed else (5, 0)


def get_work_start_time_str() -> str:
    """'05:00' formatida qaytaradi"""
    h, m = get_work_start_time()
    return f"{h:02d}:{m:02d}"


def get_daily_report_time() -> Tuple[int, int]:
    """Kunlik hisobot vaqti (ish boshlash vaqtidan 15 daqiqa keyin)"""
    h, m = get_work_start_time()
    settings = load_settings()
    offset = settings.get("report_offset_minutes", 15)
    total_minutes = (h * 60 + m + offset) % (24 * 60)
    return total_minutes // 60, total_minutes % 60


def get_daily_report_time_str() -> str:
    """'05:15' formatida qaytaradi"""
    h, m = get_daily_report_time()
    return f"{h:02d}:{m:02d}"


def set_work_start_time(hour: int, minute: int) -> bool:
    """
    Ish boshlash vaqtini o'zgartiradi, faylga yozadi va
    ishlab turgan schedulerni darhol qayta rejalashtiradi.
    """
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        logger.error(f"Noto'g'ri vaqt qiymatlari: hour={hour}, minute={minute}")
        return False

    time_str = f"{hour:02d}:{minute:02d}"
    settings = load_settings()
    settings["work_start_time"] = time_str
    success = save_settings(settings)

    if success:
        logger.info(f"✅ Ish boshlash vaqti yangilandi: {time_str}")

        # Schedulerdagi joblarni darhol yangilaymiz
        try:
            import scheduler
            scheduler.update_morning_schedule(hour, minute)
        except Exception as e:
            logger.warning(f"Schedulerni yangilashda xato: {e}")

        # WebSocket orqali barcha ulanganlarga xabar yuboramiz
        try:
            from websocket_server import ws_server
            ws_server.broadcast({
                "event": "work_schedule_updated",
                "work_start_time": time_str,
                "daily_report_time": get_daily_report_time_str()
            })
        except Exception as e:
            logger.debug(f"WS broadcast xatosi: {e}")

    return success
