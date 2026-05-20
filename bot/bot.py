#!/usr/bin/env python3
"""
Mahalla Damas Bot
=================
Mahallaga qatnayotgan damas haydovchilari uchun Telegram bot.

Arxitektura:
- bot.py          -> Asosiy kirish nuqtasi, botni ishga tushiradi
- config.py       -> Konfiguratsiya (env dan)
- api_client.py   -> Django backend bilan muloqot
- keyboards.py    -> Barcha Telegram tugmalari
- middlewares.py  -> Auth tekshiruvi (admin, driver)
- scheduler.py    -> Ertalabki avtomatik xabarlar
- handlers/
    start.py      -> /start buyrug'i
    admin.py      -> /admin buyrug'i va admin amallar
    driver.py     -> /driver buyrug'i va haydovchi amallar
"""

import logging
import telebot
from config import BOT_TOKEN
from handlers import register_all_handlers
from scheduler import setup_scheduler

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_bot() -> telebot.TeleBot:
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
    return bot


def main():
    logger.info("Mahalla Damas Bot ishga tushmoqda...")

    bot = create_bot()

    # Barcha handlerlarni ro'yxatdan o'tkazish
    register_all_handlers(bot)
    logger.info("Handlerlar ro'yxatdan o'tkazildi.")

    # Scheduler ni ishga tushirish
    setup_scheduler(bot)

    # Bot ma'lumotlarini chiqarish
    try:
        me = bot.get_me()
        logger.info(f"Bot ishga tushdi: @{me.username} ({me.id})")
    except Exception as e:
        logger.error(f"Bot ma'lumotlarini olishda xato: {e}")

    # Polling boshlash
    logger.info("Polling boshlandi...")
    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=30,
        logger_level=logging.WARNING,
        allowed_updates=['message', 'callback_query', 'my_chat_member']
    )


if __name__ == '__main__':
    main()
