#!/usr/bin/env python3
"""Mahalla Damas Bot"""
import logging
import telebot
from config import BOT_TOKEN
from handlers import register_all_handlers
from scheduler import setup_scheduler
import middlewares

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Mahalla Damas Bot ishga tushmoqda...")
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

    # Barcha xabarlarda last_seen yangilash (faqat haydovchilar uchun — xato chiqmaydi)
    @bot.middleware_handler(update_types=['message'])
    def update_last_seen_middleware(bot_instance, message):
        if message.from_user:
            middlewares.update_last_seen(message.from_user.id)

    register_all_handlers(bot)
    logger.info("Handlerlar ro'yxatdan o'tkazildi.")

    setup_scheduler(bot)

    try:
        me = bot.get_me()
        logger.info(f"Bot: @{me.username} ({me.id})")
    except Exception as e:
        logger.error(f"Bot ma'lumotlarini olishda xato: {e}")

    logger.info("Polling boshlandi...")
    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=30,
        logger_level=logging.WARNING,
        allowed_updates=['message', 'callback_query', 'my_chat_member']
    )


if __name__ == '__main__':
    main()