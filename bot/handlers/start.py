import telebot
import logging
import keyboards
import middlewares

logger = logging.getLogger(__name__)


def register_start_handlers(bot: telebot.TeleBot):

    @bot.message_handler(commands=['start'])
    def cmd_start(message):
        middlewares.register_chat(message)
        user_name = message.from_user.first_name or "Foydalanuvchi"
        
        text = (
            f"👋 Assalomu alaykum, <b>{user_name}</b>!\n\n"
            f"🚌 <b>Mahalla Damas Boti</b>ga xush kelibsiz!\n\n"
            f"Bu bot orqali siz:\n"
            f"• 📍 Haydovchilar qayerdaligini bilishingiz\n"
            f"• 📅 Bugun kim ishlayotganini ko'rishingiz\n"
            f"• 🚗 Haydovchilar haqida ma'lumot olishingiz mumkin\n\n"
            f"<b>Buyruqlar:</b>\n"
            f"/start - Botni qayta ishga tushirish\n"
            f"/driver - Haydovchi paneli\n"
            f"/admin - Admin paneli\n"
        )
        
        bot.send_message(
            message.chat.id,
            text,
            parse_mode='HTML',
            reply_markup=keyboards.main_menu_keyboard()
        )

    @bot.message_handler(func=lambda m: m.text == "ℹ️ Bot haqida")
    def bot_info(message):
        text = (
            "ℹ️ <b>Mahalla Damas Boti</b>\n\n"
            "Bu bot mahallaga qatnayotgan damas haydovchilarining "
            "joylashuvi va ish jadvalini real vaqtda ko'rish imkonini beradi.\n\n"
            "📌 Har kuni ertalab 5:00 da haydovchilarga \"Bugun ishga chiqasizmi?\" "
            "so'rovi yuboriladi.\n\n"
            "📌 5:15 da bugun ishlaydigan haydovchilar ro'yxati guruhga e'lon qilinadi."
        )
        bot.send_message(message.chat.id, text, parse_mode='HTML')
