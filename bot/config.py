from decouple import config

BOT_TOKEN = config('BOT_TOKEN')
GROUP_CHAT_ID = config('GROUP_CHAT_ID', cast=int)
BACKEND_URL = config('BACKEND_URL', default='http://backend:8000')
BACKEND_API_KEY = config('BACKEND_API_KEY', default='internal-secret-api-key')

# Admin Telegram ID lari (vergul bilan ajratilgan)
ADMIN_IDS_STR = config('ADMIN_IDS', default='')
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(',') if x.strip()]

TIMEZONE = 'Asia/Tashkent'
