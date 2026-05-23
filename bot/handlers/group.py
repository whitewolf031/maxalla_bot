"""
Guruh buyruqlari:
  /status  — bugun kimlar ishlayapti
  /drivers — barcha haydovchilar ro'yxati
"""
import telebot
import logging
import api_client
from scheduler import now_tashkent, today_tashkent

logger = logging.getLogger(__name__)


def register_group_handlers(bot: telebot.TeleBot):

    @bot.message_handler(commands=['status'])
    def cmd_status(message):
        working = api_client.get_today_statuses(status='working')
        today = today_tashkent()
        now = now_tashkent()

        if not working:
            bot.send_message(
                message.chat.id,
                f"📅 <b>{today} — Bugungi holat</b>\n\n"
                f"Bugun hali hech kim ishga chiqmagan.\n"
                f"🕐 {now}",
                parse_mode='HTML'
            )
            return

        text = f"📅 <b>{today} — Bugun ishlaydigan haydovchilar ({len(working)} ta):</b>\n\n"
        for i, d in enumerate(working, 1):
            loc = f"\n    📍 {d['location']}" if d.get('location') else ""
            mov = ""
            if d.get('moving_direction') == 'mahalla_to_oydin':
                mov = "\n    🚗 Oydin tomonga ketmoqda"
            elif d.get('moving_direction') == 'oydin_to_mahalla':
                mov = "\n    ↩️ Mahalla tomonga qaytmoqda"
            elif d.get('moving_direction') == 'finished':
                mov = "\n    🏁 Ishni tugatgan"

            text += (
                f"{i}. 👤 <b>{d['driver_name']}</b>\n"
                f"    📞 {d['driver_phone']}\n"
                f"    🚙 {d['car_name']} | <code>{d['car_number']}</code>{loc}{mov}\n\n"
            )
        text += f"🕐 {now}"

        bot.send_message(message.chat.id, text, parse_mode='HTML')

    @bot.message_handler(commands=['drivers'])
    def cmd_drivers(message):
        drivers = api_client.get_approved_drivers()
        now = now_tashkent()

        if not drivers:
            bot.send_message(message.chat.id, "📋 Hozirda tasdiqlangan haydovchilar yo'q.")
            return

        text = f"🚌 <b>Mahalla liniya haydovchilari ({len(drivers)} ta):</b>\n\n"
        for i, d in enumerate(drivers, 1):
            text += (
                f"━━━━━━━━━━━━━━━━\n"
                f"{i}. 👤 <b>{d['full_name']}</b>\n"
                f"    📞 {d['phone_number']}\n"
                f"    🚗 {d['car_name']} | <code>{d['car_number']}</code>\n"
            )
        text += f"━━━━━━━━━━━━━━━━\n🕐 {now}"

        bot.send_message(message.chat.id, text, parse_mode='HTML')