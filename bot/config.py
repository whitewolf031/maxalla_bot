from decouple import config

BOT_TOKEN = config('BOT_TOKEN')
GROUP_CHAT_ID = config('GROUP_CHAT_ID', cast=int)
BACKEND_URL = config('BACKEND_URL', default='http://backend:8000')
BACKEND_API_KEY = config('BACKEND_API_KEY', default='internal-secret-api-key')

# Admin Telegram ID lari (vergul bilan ajratilgan)
ADMIN_IDS_STR = config('ADMIN_IDS', default='')
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(',') if x.strip()]

TIMEZONE = 'Asia/Tashkent'

# WebSocket sozlamalari
WS_HOST = config('WS_HOST', default='0.0.0.0')
WS_PORT = config('WS_PORT', default=8765, cast=int)

# Haydovchilardan joylashuv so'rash vaqti va oralig'i (daqiqa)
LOCATION_PROMPT_INTERVAL_MINUTES = config('LOCATION_PROMPT_INTERVAL_MINUTES', default=30, cast=int)
LOCATION_PROMPT_START_HOUR = config('LOCATION_PROMPT_START_HOUR', default=6, cast=int)
LOCATION_PROMPT_END_HOUR = config('LOCATION_PROMPT_END_HOUR', default=21, cast=int)
