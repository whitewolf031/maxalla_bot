import telebot
import logging
import keyboards
import middlewares
import api_client

logger = logging.getLogger(__name__)

# Elon kutish holati
waiting_for_announcement = set()


def register_admin_handlers(bot: telebot.TeleBot):

    @bot.message_handler(commands=['admin'])
    def cmd_admin(message):
        if not middlewares.is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Sizda admin huquqlari yo'q.")
            return
        
        bot.send_message(
            message.chat.id,
            "🛡️ <b>Admin paneli</b>\n\nQuyidagi amallardan birini tanlang:",
            parse_mode='HTML',
            reply_markup=keyboards.admin_menu_keyboard()
        )

    @bot.message_handler(func=lambda m: m.text == "📋 Kutayotgan so'rovlar" and middlewares.is_admin(m.from_user.id))
    def pending_requests(message):
        drivers = api_client.get_pending_drivers()
        
        if not drivers:
            bot.send_message(message.chat.id, "✅ Hozirda kutayotgan so'rovlar yo'q.")
            return
        
        bot.send_message(message.chat.id, f"📋 <b>Kutayotgan so'rovlar: {len(drivers)} ta</b>", parse_mode='HTML')
        
        for driver in drivers:
            text = (
                f"👤 <b>{driver['full_name']}</b>\n"
                f"📞 {driver['phone_number']}\n"
                f"🚗 {driver['car_name']} - {driver['car_number']}\n"
                f"🆔 Telegram ID: <code>{driver['telegram_id']}</code>"
            )
            bot.send_message(
                message.chat.id,
                text,
                parse_mode='HTML',
                reply_markup=keyboards.driver_approval_keyboard(driver['id'])
            )

    @bot.message_handler(func=lambda m: m.text == "✅ Tasdiqlangan haydovchilar" and middlewares.is_admin(m.from_user.id))
    def approved_drivers_admin(message):
        drivers = api_client.get_approved_drivers()
        
        if not drivers:
            bot.send_message(message.chat.id, "📋 Hozirda tasdiqlangan haydovchilar yo'q.")
            return
        
        text = f"✅ <b>Tasdiqlangan haydovchilar ({len(drivers)} ta):</b>\n\n"
        for i, d in enumerate(drivers, 1):
            text += (
                f"{i}. <b>{d['full_name']}</b>\n"
                f"   📞 {d['phone_number']}\n"
                f"   🚗 {d['car_name']} | {d['car_number']}\n\n"
            )
        
        bot.send_message(message.chat.id, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "📊 Bugungi holat" and middlewares.is_admin(m.from_user.id))
    def today_status_admin(message):
        working = api_client.get_today_statuses(status='working')
        not_working = api_client.get_today_statuses(status='not_working')
        pending = api_client.get_today_statuses(status='pending')
        
        text = "📊 <b>Bugungi holat:</b>\n\n"
        
        text += f"✅ <b>Ishlamoqda ({len(working)} ta):</b>\n"
        for d in working:
            loc = f" ({d.get('location', '')})" if d.get('location') else ""
            text += f"  • {d['driver_name']} - {d['car_number']}{loc}\n"
        
        text += f"\n❌ <b>Ishlamayapti ({len(not_working)} ta):</b>\n"
        for d in not_working:
            text += f"  • {d['driver_name']}\n"
        
        if pending:
            text += f"\n⏳ <b>Javob bermagan ({len(pending)} ta):</b>\n"
            for d in pending:
                text += f"  • {d['driver_name']}\n"
        
        bot.send_message(message.chat.id, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "📢 Elon tarqatish" and middlewares.is_admin(m.from_user.id))
    def start_announcement(message):
        waiting_for_announcement.add(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "📢 <b>Elon matni</b>ni kiriting:\n\n(Bekor qilish uchun /cancel yozing)",
            parse_mode='HTML',
            reply_markup=keyboards.cancel_keyboard()
        )

    @bot.message_handler(func=lambda m: m.from_user.id in waiting_for_announcement)
    def process_announcement(message):
        if message.text == "❌ Bekor qilish":
            waiting_for_announcement.discard(message.from_user.id)
            bot.send_message(message.chat.id, "❌ Bekor qilindi.", reply_markup=keyboards.admin_menu_keyboard())
            return
        
        if not middlewares.is_admin(message.from_user.id):
            waiting_for_announcement.discard(message.from_user.id)
            return

        waiting_for_announcement.discard(message.from_user.id)
        announcement_text = message.text
        
        chat_ids = api_client.get_all_chat_ids()
        
        sent = 0
        failed = 0
        
        full_text = f"📢 <b>ELON</b>\n\n{announcement_text}"
        
        for chat_id in chat_ids:
            try:
                bot.send_message(chat_id, full_text, parse_mode='HTML')
                sent += 1
            except Exception as e:
                logger.warning(f"Chat {chat_id} ga yuborishda xato: {e}")
                failed += 1
        
        api_client.save_announcement(announcement_text, message.from_user.id, sent)
        
        bot.send_message(
            message.chat.id,
            f"✅ Elon {sent} ta chat ga yuborildi.\n❌ {failed} ta xato.",
            reply_markup=keyboards.admin_menu_keyboard()
        )

    # ---- Callback handlers ----

    @bot.callback_query_handler(func=lambda c: c.data.startswith('approve_driver:'))
    def approve_driver_cb(call):
        if not middlewares.is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Ruxsat yo'q!")
            return
        
        driver_id = int(call.data.split(':')[1])
        result = api_client.approve_driver(driver_id)
        
        if result:
            driver = result.get('driver', {})
            
            # Haydovchiga xabar yuborish
            try:
                bot.send_message(
                    driver['telegram_id'],
                    "✅ <b>Tabriklaymiz!</b>\n\nSizning haydovchi sifatida so'rovingiz tasdiqlandi!\n"
                    "Endi /driver buyrug'i orqali haydovchi panelidan foydalanishingiz mumkin.",
                    parse_mode='HTML'
                )
            except Exception:
                pass
            
            bot.edit_message_text(
                f"✅ <b>{driver.get('full_name', '')}</b> tasdiqlandi!",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
        
        bot.answer_callback_query(call.id, "✅ Tasdiqlandi!")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('reject_driver:'))
    def reject_driver_cb(call):
        if not middlewares.is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Ruxsat yo'q!")
            return
        
        driver_id = int(call.data.split(':')[1])
        result = api_client.reject_driver(driver_id)
        
        if result:
            bot.edit_message_text(
                f"❌ Haydovchi rad etildi.",
                call.message.chat.id,
                call.message.message_id,
            )
        
        bot.answer_callback_query(call.id, "❌ Rad etildi.")
