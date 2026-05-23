import logging
from config import ADMIN_IDS
import api_client

logger = logging.getLogger(__name__)


def is_admin(telegram_id: int) -> bool:
    return int(telegram_id) in ADMIN_IDS


def is_approved_driver(telegram_id: int) -> bool:
    driver = api_client.get_driver_by_telegram(telegram_id)
    return bool(driver and driver.get('status') == 'approved')


def get_driver(telegram_id: int):
    return api_client.get_driver_by_telegram(telegram_id)


def register_chat(message):
    """Foydalanuvchi yoki guruhni ro'yxatdan o'tkazish"""
    try:
        is_group = message.chat.type in ['group', 'supergroup', 'channel']
        api_client.register_user(
            telegram_id=message.chat.id,
            username=getattr(message.chat, 'username', None),
            first_name=getattr(message.chat, 'first_name', None),
            last_name=getattr(message.chat, 'last_name', None),
            is_group=is_group
        )
    except Exception as e:
        logger.error(f"Ro'yxatdan o'tkazishda xato: {e}")


def update_last_seen(telegram_id: int):
    """Haydovchi har xabar yuborganda oxirgi faollik vaqtini yangilash"""
    try:
        api_client.update_last_seen(telegram_id)
    except Exception as e:
        logger.debug(f"last_seen yangilashda xato: {e}")