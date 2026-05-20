import requests
import logging
from config import BACKEND_URL, BACKEND_API_KEY

logger = logging.getLogger(__name__)

HEADERS = {
    'Content-Type': 'application/json',
    'X-API-Key': BACKEND_API_KEY,
}


def _get(endpoint, params=None):
    try:
        url = f"{BACKEND_URL}/{endpoint}"
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"GET {endpoint} xatosi: {e}")
        return None


def _post(endpoint, data):
    try:
        url = f"{BACKEND_URL}/{endpoint}"
        r = requests.post(url, headers=HEADERS, json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"POST {endpoint} xatosi: {e}")
        return None


# ---- Drivers ----

def get_all_drivers(status=None):
    params = {}
    if status:
        params['status'] = status
    return _get('api/drivers/', params=params) or []


def get_approved_drivers():
    return _get('api/drivers/approved/') or []


def get_pending_drivers():
    return _get('api/drivers/pending/') or []


def get_driver_by_telegram(telegram_id):
    return _get(f'api/drivers/telegram/{telegram_id}/')


def register_driver(data):
    return _post('api/drivers/create/', data)


def approve_driver(driver_id):
    return _post(f'api/drivers/{driver_id}/approve/', {})


def reject_driver(driver_id):
    return _post(f'api/drivers/{driver_id}/reject/', {})


# ---- Daily Status ----

def set_daily_status(telegram_id, status, location=None, moving_direction=None):
    data = {'telegram_id': telegram_id, 'status': status}
    if location:
        data['location'] = location
    if moving_direction:
        data['moving_direction'] = moving_direction
    return _post('api/drivers/status/set/', data)


def get_today_statuses(status=None, location=None):
    params = {}
    if status:
        params['status'] = status
    if location:
        params['location'] = location
    return _get('api/drivers/status/today/', params=params) or []


def get_working_drivers_today():
    return _get('api/drivers/status/working/') or []


def update_driver_location(telegram_id, location, moving_direction=None):
    data = {'telegram_id': telegram_id, 'location': location}
    if moving_direction:
        data['moving_direction'] = moving_direction
    return _post('api/drivers/status/location/', data)


# ---- Users ----

def register_user(telegram_id, username=None, first_name=None, last_name=None, is_group=False):
    return _post('api/users/register/', {
        'telegram_id': telegram_id,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'is_group': is_group,
    })


def get_all_chat_ids():
    result = _get('api/users/chat-ids/')
    if result:
        return result.get('chat_ids', [])
    return []


# ---- Announcements ----

def save_announcement(text, sent_by, recipients_count):
    return _post('api/announcements/', {
        'text': text,
        'sent_by': sent_by,
        'recipients_count': recipients_count,
    })
