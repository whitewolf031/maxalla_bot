import telebot
import logging
import keyboards
import middlewares
import api_client
import bot_settings

logger = logging.getLogger(__name__)

# Elon kutish holati
waiting_for_announcement = set()

# Ish boshlash vaqtini kiritish holati
waiting_for_work_time = set()


def register_admin_handlers(bot: telebot.TeleBot):

    @bot.message_handler(commands=['admin'])
    def cmd_admin(message):
        if not middlewares.is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Sizda admin huquqlari yo'q.")
            return

        start_str = bot_settings.get_work_start_time_str()
        rep_str = bot_settings.get_daily_report_time_str()

        bot.send_message(
            message.chat.id,
            f"🛡️ <b>Admin paneli</b>\n\n"
            f"⏰ <b>Ertalabki ish vaqti:</b> <code>{start_str}</code> (Hisobot: <code>{rep_str}</code>)\n\n"
            f"Quyidagi amallardan birini tanlang:",
            parse_mode='HTML',
            reply_markup=keyboards.admin_menu_keyboard()
        )

    # ── Ish boshlash vaqti sozlamalari ───────────────────────

    @bot.message_handler(func=lambda m: m.text == "⏰ Ish boshlash vaqti" and middlewares.is_admin(m.from_user.id))
    def show_work_time_menu(message):
        start_str = bot_settings.get_work_start_time_str()
        rep_str = bot_settings.get_daily_report_time_str()

        text = (
            f"⏰ <b>Ertalabki ish boshlash vaqti sozlamalari</b>\n\n"
            f"🌅 <b>Hozirgi vaqt:</b> <code>{start_str}</code> (Har kuni ertalab)\n"
            f"📊 <b>Guruhga hisobot vaqti:</b> <code>{rep_str}</code> (15 daqiqadan so'ng)\n\n"
            f"ℹ️ Har kuni ertalab <b>{start_str}</b> da barcha tasdiqlangan haydovchilarga "
            f"<i>\"Bugun ishga chiqasizmi?\"</i> so'rovi avtomatik yuboriladi.\n\n"
            f"<b>{rep_str}</b> da esa javob berganlar ro'yxati guruhga e'lon qilinadi "
            f"va javob bermaganlar avtomatik <i>ishlamayapti</i> deb belgilanadi.\n\n"
            f"Vaqtni o'zgartirish uchun quyidagi tugmani bosing:"
        )
        bot.send_message(
            message.chat.id,
            text,
            parse_mode='HTML',
            reply_markup=keyboards.work_time_view_keyboard()
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith('work_time:'))
    def work_time_callback(call):
        if not middlewares.is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Ruxsat yo'q!")
            return

        action = call.data.split(':', 1)[1]

        if action == 'change':
            start_str = bot_settings.get_work_start_time_str()
            bot.edit_message_text(
                f"⏰ <b>Ish boshlash vaqtini tanlang yoki yangi vaqt kiriting:</b>\n\n"
                f"Joriy vaqt: <code>{start_str}</code>",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                reply_markup=keyboards.work_time_change_keyboard()
            )
            bot.answer_callback_query(call.id)
            return

        if action.startswith('set:'):
            time_val = action.split(':', 1)[1]
            parsed = bot_settings.parse_time_str(time_val)
            if parsed:
                h, m = parsed
                bot_settings.set_work_start_time(h, m)
                start_str = bot_settings.get_work_start_time_str()
                rep_str = bot_settings.get_daily_report_time_str()

                bot.edit_message_text(
                    f"✅ <b>Ish boshlash vaqti muvaffaqiyatli o'zgartirildi!</b>\n\n"
                    f"🌅 <b>Yangi vaqt:</b> <code>{start_str}</code>\n"
                    f"📊 <b>Guruhga hisobot vaqti:</b> <code>{rep_str}</code>\n\n"
                    f"Endi har kuni soat <b>{start_str}</b> da haydovchilarga so'rov yuboriladi.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML',
                    reply_markup=keyboards.work_time_view_keyboard()
                )
                bot.answer_callback_query(call.id, f"✅ Vaqt {start_str} ga o'rnatildi!")
            else:
                bot.answer_callback_query(call.id, "Xato: vaqt formati noto'g'ri!")
            return

        if action == 'custom':
            waiting_for_work_time.add(call.from_user.id)
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "⌨️ <b>Yangi ish boshlash vaqtini kiriting:</b>\n\n"
                "Format: <code>HH:MM</code> (masalan: <code>05:45</code> yoki <code>06:15</code>)\n\n"
                "(Bekor qilish uchun <b>❌ Bekor qilish</b> tugmasini bosing)",
                parse_mode='HTML',
                reply_markup=keyboards.cancel_keyboard()
            )
            return

        if action == 'cancel':
            waiting_for_work_time.discard(call.from_user.id)
            start_str = bot_settings.get_work_start_time_str()
            rep_str = bot_settings.get_daily_report_time_str()
            bot.edit_message_text(
                f"⏰ <b>Ertalabki ish boshlash vaqti sozlamalari</b>\n\n"
                f"🌅 <b>Hozirgi vaqt:</b> <code>{start_str}</code>\n"
                f"📊 <b>Guruhga hisobot vaqti:</b> <code>{rep_str}</code>",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                reply_markup=keyboards.work_time_view_keyboard()
            )
            bot.answer_callback_query(call.id, "Bekor qilindi.")
            return

    @bot.message_handler(func=lambda m: m.from_user.id in waiting_for_work_time)
    def process_custom_work_time(message):
        if message.text == "❌ Bekor qilish":
            waiting_for_work_time.discard(message.from_user.id)
            bot.send_message(message.chat.id, "❌ Bekor qilindi.", reply_markup=keyboards.admin_menu_keyboard())
            return

        parsed = bot_settings.parse_time_str(message.text.strip())
        if not parsed:
            bot.send_message(
                message.chat.id,
                "❌ <b>Noto'g'ri vaqt formati!</b>\n\n"
                "Iltimos, vaqtni <b>HH:MM</b> ko'rinishida kiriting (masalan: <code>05:45</code> yoki <code>06:00</code>):\n\n"
                "(Bekor qilish uchun: ❌ Bekor qilish)",
                parse_mode='HTML',
                reply_markup=keyboards.cancel_keyboard()
            )
            return

        waiting_for_work_time.discard(message.from_user.id)
        h, m = parsed
        bot_settings.set_work_start_time(h, m)
        start_str = bot_settings.get_work_start_time_str()
        rep_str = bot_settings.get_daily_report_time_str()

        bot.send_message(
            message.chat.id,
            f"✅ <b>Ish boshlash vaqti muvaffaqiyatli o'zgartirildi!</b>\n\n"
            f"🌅 <b>Yangi vaqt:</b> <code>{start_str}</code>\n"
            f"📊 <b>Guruhga hisobot vaqti:</b> <code>{rep_str}</code>\n\n"
            f"Endi har kuni soat <b>{start_str}</b> da haydovchilarga so'rov yuboriladi va "
            f"<b>{rep_str}</b> da guruhga hisobot beriladi.",
            parse_mode='HTML',
            reply_markup=keyboards.admin_menu_keyboard()
        )

    # ── So'rovlar va ro'yxat ──────────────────────────────────

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

        # DB dan barcha chat_id larni olish
        chat_ids = api_client.get_all_chat_ids()
        logger.info(f"Elon uchun {len(chat_ids)} ta chat_id olindi: {chat_ids}")

        # Guruh har doim ro'yxatda bo'lishi uchun qo'shamiz
        from config import GROUP_CHAT_ID
        if GROUP_CHAT_ID not in chat_ids:
            chat_ids.append(GROUP_CHAT_ID)

        sent = 0
        failed = 0
        full_text = f"📢 <b>ELON</b>\n\n{announcement_text}"

        for chat_id in chat_ids:
            try:
                bot.send_message(chat_id, full_text, parse_mode='HTML')
                sent += 1
                logger.info(f"  -> {chat_id} ga yuborildi")
            except Exception as e:
                logger.warning(f"Chat {chat_id} ga yuborishda xato: {e}")
                failed += 1

        api_client.save_announcement(announcement_text, message.from_user.id, sent)

        bot.send_message(
            message.chat.id,
            f"✅ Elon <b>{sent}</b> ta chat ga yuborildi.\n❌ {failed} ta xato.",
            parse_mode='HTML',
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
            except Exception as e:
                logger.warning(f"Haydovchiga ({driver.get('telegram_id')}) tasdiqlash xabari yuborishda xato: {e}")

            bot.edit_message_text(
                f"✅ <b>{driver.get('full_name', '')}</b> tasdiqlandi!",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )

            # WebSocket broadcast
            try:
                from websocket_server import ws_server
                ws_server.broadcast({
                    "event": "driver_approved",
                    "driver_id": driver_id,
                    "driver_name": driver.get('full_name'),
                    "telegram_id": driver.get('telegram_id')
                })
            except Exception:
                pass

        bot.answer_callback_query(call.id, "✅ Tasdiqlandi!")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('reject_driver:'))
    def reject_driver_cb(call):
        if not middlewares.is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Ruxsat yo'q!")
            return

        driver_id = int(call.data.split(':')[1])
        result = api_client.reject_driver(driver_id)

        if result:
            driver = result.get('driver', {})
            tg_id = driver.get('telegram_id')
            if tg_id:
                try:
                    bot.send_message(
                        tg_id,
                        "❌ <b>Afsuski, sizning so'rovingiz rad etildi.</b>\n\n"
                        "Ma'lumotlaringizni to'g'rilab /driver orqali qayta ariza topshirishingiz mumkin.",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.warning(f"Haydovchiga ({tg_id}) rad etish xabarini yuborishda xato: {e}")

            bot.edit_message_text(
                f"❌ <b>{driver.get('full_name', 'Haydovchi')}</b> rad etildi.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )

            # WebSocket broadcast
            try:
                from websocket_server import ws_server
                ws_server.broadcast({
                    "event": "driver_rejected",
                    "driver_id": driver_id,
                    "driver_name": driver.get('full_name'),
                    "telegram_id": tg_id
                })
            except Exception:
                pass

        bot.answer_callback_query(call.id, "❌ Rad etildi.")