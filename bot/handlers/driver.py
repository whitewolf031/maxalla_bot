import telebot
import logging
import keyboards
import middlewares
import api_client
from telebot import types
from config import GROUP_CHAT_ID
from scheduler import now_tashkent, today_tashkent

logger = logging.getLogger(__name__)

# Registration state management
user_states = {}
registration_data = {}


def register_driver_handlers(bot: telebot.TeleBot):

    # ── /driver buyrug'i ─────────────────────────────────────

    @bot.message_handler(commands=['driver'])
    @bot.message_handler(func=lambda m: m.text == "🚗 Haydovchi paneli")
    def cmd_driver(message):
        driver = middlewares.get_driver(message.from_user.id)

        if not driver:
            _start_registration(bot, message)
            return

        status = driver.get('status')

        if status == 'pending':
            bot.send_message(message.chat.id,
                             "⏳ Sizning so'rovingiz hali ko'rib chiqilmagan.\n"
                             "Admin tasdiqlashini kuting.")
            return

        if status == 'rejected':
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📝 Qayta ariza topshirish", callback_data=f"reregister:{message.from_user.id}"))
            bot.send_message(
                message.chat.id,
                "❌ Sizning so'rovingiz rad etilgan.\n\n"
                "Qaytadan ma'lumotlaringizni to'g'rilab ariza topshirishingiz mumkin:",
                reply_markup=markup
            )
            return

        if status == 'approved':
            bot.send_message(
                message.chat.id,
                f"🚗 <b>Haydovchi paneli</b>\n\n"
                f"Xush kelibsiz, <b>{driver['full_name']}</b>!\n"
                f"🚙 {driver['car_name']} | {driver['car_number']}",
                parse_mode='HTML',
                reply_markup=keyboards.driver_menu_keyboard()
            )

    # ── Ro'yxatdan o'tish ────────────────────────────────────

    def _start_registration(bot, message):
        uid = message.from_user.id
        user_states[uid] = 'waiting_full_name'
        registration_data[uid] = {}
        bot.send_message(
            message.chat.id,
            "📝 <b>Haydovchi sifatida ro'yxatdan o'tish</b>\n\n"
            "To'liq ismingizni kiriting (Familiya Ism Otasining ismi):",
            parse_mode='HTML',
            reply_markup=types.ReplyKeyboardRemove()
        )

    @bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_full_name')
    def process_full_name(message):
        uid = message.from_user.id
        registration_data[uid]['full_name'] = message.text.strip()
        user_states[uid] = 'waiting_phone'
        bot.send_message(
            message.chat.id,
            "📞 Telefon raqamingizni kiriting (+998XXXXXXXXX):",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                types.KeyboardButton("📞 Raqamni ulashish", request_contact=True)
            )
        )

    @bot.message_handler(content_types=['contact'],
                         func=lambda m: user_states.get(m.from_user.id) == 'waiting_phone')
    def process_contact(message):
        uid = message.from_user.id
        phone = message.contact.phone_number
        if not phone.startswith('+'):
            phone = '+' + phone
        registration_data[uid]['phone_number'] = phone
        user_states[uid] = 'waiting_car_name'
        bot.send_message(message.chat.id, "🚗 Avtomobil nomini kiriting (masalan: Damas):",
                         reply_markup=types.ReplyKeyboardRemove())

    @bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_phone')
    def process_phone(message):
        uid = message.from_user.id
        registration_data[uid]['phone_number'] = message.text.strip()
        user_states[uid] = 'waiting_car_name'
        bot.send_message(message.chat.id, "🚗 Avtomobil nomini kiriting (masalan: Damas):",
                         reply_markup=types.ReplyKeyboardRemove())

    @bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_car_name')
    def process_car_name(message):
        uid = message.from_user.id
        registration_data[uid]['car_name'] = message.text.strip()
        user_states[uid] = 'waiting_car_number'
        bot.send_message(message.chat.id, "🔢 Avtomobil raqamini kiriting (masalan: 01 A 123 BA):")

    @bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_car_number')
    def process_car_number(message):
        uid = message.from_user.id
        registration_data[uid]['car_number'] = message.text.strip().upper()
        data = registration_data[uid]

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"reg_confirm:{uid}"),
            types.InlineKeyboardButton("❌ Bekor",      callback_data=f"reg_cancel:{uid}")
        )
        user_states[uid] = 'waiting_confirm'
        bot.send_message(
            message.chat.id,
            f"✅ <b>Ma'lumotlaringizni tasdiqlang:</b>\n\n"
            f"👤 Ism: <b>{data['full_name']}</b>\n"
            f"📞 Telefon: <b>{data['phone_number']}</b>\n"
            f"🚗 Avtomobil: <b>{data['car_name']}</b>\n"
            f"🔢 Raqam: <b>{data['car_number']}</b>\n\n"
            f"Yuborish uchun ✅ ni bosing:",
            parse_mode='HTML', reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith('reregister:'))
    def reregister_callback(call):
        uid = int(call.data.split(':')[1])
        if call.from_user.id != uid:
            bot.answer_callback_query(call.id, "Ruxsat yo'q!")
            return
        bot.answer_callback_query(call.id)
        _start_registration(bot, call.message)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('reg_confirm:'))
    def confirm_registration(call):
        uid = int(call.data.split(':')[1])
        if call.from_user.id != uid:
            bot.answer_callback_query(call.id, "Bu sizning so'rovingiz emas!")
            return

        data = registration_data.get(uid, {})
        data['telegram_id'] = uid
        data['telegram_username'] = call.from_user.username

        logger.info(f"Haydovchi ro'yxatdan o'tmoqda: telegram_id={uid}, data={data}")
        result = api_client.register_driver(data)
        logger.info(f"Backend register_driver javobi: {result}")

        if not result:
            bot.answer_callback_query(call.id, "Xatolik yuz berdi. Backend bilan aloqa yo'q.")
            return

        # Agar allaqachon tasdiqlangan bo'lsa
        if result.get('status') == 'approved':
            user_states.pop(uid, None)
            registration_data.pop(uid, None)
            bot.edit_message_text(
                "✅ Siz allaqachon tasdiqlangan haydovchisiz!\n\n"
                "/driver buyrug'i orqali haydovchi paneliga kirishingiz mumkin.",
                call.message.chat.id, call.message.message_id
            )
            return

        driver_id = result.get('id')
        if not driver_id and 'driver' in result and isinstance(result['driver'], dict):
            driver_id = result['driver'].get('id')

        if not driver_id:
            logger.error(f"register_driver javobida 'id' topilmadi: {result}")
            bot.answer_callback_query(call.id, "So'rov yuborishda xatolik yuz berdi.")
            return

        # Ro'yxatdan o'tish muvaffaqiyatli
        user_states.pop(uid, None)
        registration_data.pop(uid, None)

        bot.edit_message_text(
            "✅ <b>So'rovingiz qabul qilindi va adminga yuborildi!</b>\n\n"
            "⏳ Admin ko'rib chiqadi va tasdiqlaydi.\n"
            "Tasdiqlangandan so'ng sizga xabar yuboriladi.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )

        full_name = data.get('full_name') or result.get('full_name', 'Noma\'lum')
        phone_number = data.get('phone_number') or result.get('phone_number', 'Noma\'lum')
        car_name = data.get('car_name') or result.get('car_name', 'Noma\'lum')
        car_number = data.get('car_number') or result.get('car_number', 'Noma\'lum')
        username_str = f"@{call.from_user.username}" if call.from_user.username else "Yo'q"

        admin_text = (
            f"🆕 <b>Yangi haydovchi so'rovi!</b>\n\n"
            f"👤 Ism: <b>{full_name}</b>\n"
            f"📞 Telefon: <b>{phone_number}</b>\n"
            f"🚗 Avtomobil: <b>{car_name}</b> | <code>{car_number}</code>\n"
            f"🌐 Username: {username_str}\n"
            f"🆔 Telegram ID: <code>{uid}</code>\n"
            f"🔢 Haydovchi ID: <code>{driver_id}</code>"
        )

        from config import ADMIN_IDS
        if not ADMIN_IDS:
            logger.warning("DIQQAT: ADMIN_IDS ro'yxati bo'sh! Yangi haydovchi so'rovi hech kimga yuborilmadi.")

        sent_to_admins = 0
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(
                    admin_id,
                    admin_text,
                    parse_mode='HTML',
                    reply_markup=keyboards.driver_approval_keyboard(driver_id)
                )
                sent_to_admins += 1
                logger.info(f"✅ Yangi haydovchi so'rovi adminga ({admin_id}) muvaffaqiyatli yuborildi.")
            except Exception as e:
                logger.error(
                    f"❌ Adminga ({admin_id}) haydovchi so'rovini yuborishda xatolik: {e}. "
                    f"Eslatma: Admin botga kamida bir marta /start bosgan bo'lishi shart!"
                )

        # WebSocket mijozlariga broadcast
        try:
            from websocket_server import ws_server
            ws_server.broadcast({
                "event": "new_driver_application",
                "driver_id": driver_id,
                "telegram_id": uid,
                "full_name": full_name,
                "phone_number": phone_number,
                "car_name": car_name,
                "car_number": car_number,
                "status": "pending"
            })
        except Exception as e:
            logger.debug(f"WS broadcast xatosi: {e}")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('reg_cancel:'))
    def cancel_registration(call):
        uid = int(call.data.split(':')[1])
        user_states.pop(uid, None)
        registration_data.pop(uid, None)
        bot.edit_message_text("❌ Ro'yxatdan o'tish bekor qilindi.",
                              call.message.chat.id, call.message.message_id)

    # ── Haydovchi menyu tugmalari ────────────────────────────

    @bot.message_handler(func=lambda m: m.text == "📊 Mening statusim")
    def my_status(message):
        if not middlewares.is_approved_driver(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Bu funksiya faqat tasdiqlangan haydovchilar uchun.")
            return

        driver = middlewares.get_driver(message.from_user.id)
        if not driver:
            return

        today_statuses = api_client.get_today_statuses()
        my = next((s for s in today_statuses
                   if str(s.get('driver')) == str(driver.get('id'))), None)

        if my:
            icons = {'working': '✅ Ishlamoqda', 'not_working': '❌ Ishlamayapti', 'pending': '⏳ Javob berilmagan'}
            status_text = icons.get(my['status'], my['status'])
            loc = f"\n📍 Joylashuv: {my['location']}" if my.get('location') else ""
            text = (
                f"📊 <b>Bugungi holatingiz:</b>\n\n"
                f"{status_text}{loc}\n\n"
                f"📅 {today_tashkent()}"
            )
        else:
            text = (
                f"📊 <b>Bugungi holatingiz:</b>\n\n"
                f"⏳ Hali belgilanmagan\n\n"
                f"📅 {today_tashkent()}"
            )

        bot.send_message(
            message.chat.id, text,
            parse_mode='HTML',
            reply_markup=keyboards.my_status_actions_keyboard()
        )

    # ── Ishni boshlash / tugatish (manual, istalgan vaqtda) ──

    @bot.callback_query_handler(func=lambda c: c.data.startswith('workshift:'))
    def workshift_cb(call):
        action = call.data.split(':')[1]  # 'start' yoki 'end'

        driver = middlewares.get_driver(call.from_user.id)
        if not driver or driver.get('status') != 'approved':
            bot.answer_callback_query(call.id, "⛔ Siz ro'yxatda yo'qsiz!")
            return

        now = now_tashkent()
        phone = driver.get('phone_number', '')
        phone_line = f"📞 Tel: {phone}\n" if phone else ""

        if action == 'start':
            # Ishni boshlash — working statusga o'tkazish
            api_client.set_daily_status(call.from_user.id, 'working')
            api_client.update_driver_location(call.from_user.id, None, None)  # finished ni tozalaymiz

            group_text = (
                f"🟢 <b>{driver['full_name']}</b> ishni boshladi!\n"
                f"🚗 {driver['car_name']} | <code>{driver['car_number']}</code>\n"
                f"{phone_line}"
                f"🕐 {now}"
            )
            personal_text = f"✅ Ishni boshladingiz deb belgilandi.\n🕐 {now}"
            bot.answer_callback_query(call.id, "✅ Ish boshlandi!")

        else:  # end
            # Ishni tugatish — faqat working bo'lsa mumkin
            today_statuses = api_client.get_today_statuses()
            my = next((s for s in today_statuses
                       if str(s.get('driver')) == str(driver.get('id'))), None)

            if not my or my['status'] != 'working':
                bot.answer_callback_query(
                    call.id,
                    "⛔ Ishni tugatish uchun avval ishga chiqgan bo'lishingiz kerak!",
                    show_alert=True
                )
                return

            api_client.update_driver_location(call.from_user.id, None, 'finished')

            group_text = (
                f"🔴 <b>{driver['full_name']}</b> ishni tugatdi.\n"
                f"🚗 {driver['car_name']} | <code>{driver['car_number']}</code>\n"
                f"{phone_line}"
                f"🕐 {now}"
            )
            personal_text = f"✅ Ishni tugatdingiz deb belgilandi.\n🕐 {now}"
            bot.answer_callback_query(call.id, "✅ Ish tugadi!")

        # Guruhga xabar
        try:
            bot.send_message(GROUP_CHAT_ID, group_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Guruhga xabar yuborishda xato: {e}")

        bot.send_message(call.message.chat.id, personal_text, parse_mode='HTML')

    # ── Ertalabki checkin callback ────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith('checkin:'))
    def daily_checkin_cb(call):
        answer = call.data.split(':')[1]

        driver = middlewares.get_driver(call.from_user.id)
        if not driver or driver.get('status') != 'approved':
            bot.answer_callback_query(call.id, "⛔ Siz ro'yxatda yo'qsiz!")
            return

        now = now_tashkent()

        if answer == 'yes':
            api_client.set_daily_status(call.from_user.id, 'working')
            bot.edit_message_text(
                f"✅ <b>{driver['full_name']}</b>, bugun ish ro'yxatiga qo'shildingiz!\n"
                f"🚗 {driver['car_name']} | {driver['car_number']}\n"
                f"🕐 {now}",
                call.message.chat.id, call.message.message_id,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "✅ Ro'yxatga qo'shildingiz!")
        else:
            api_client.set_daily_status(call.from_user.id, 'not_working')
            bot.edit_message_text(
                f"❌ <b>{driver['full_name']}</b>, bugun ishlamaysiz deb belgilandi.\n"
                f"🕐 {now}\n\nDam oling! 😊",
                call.message.chat.id, call.message.message_id,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "❌ Belgilandi.")

    # ── Kechki checkin callback ───────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith('evening:'))
    def evening_checkin_cb(call):
        # format: evening:yes:20:00
        parts = call.data.split(':')
        answer = parts[1]
        slot   = f"{parts[2]}:{parts[3]}"

        driver = middlewares.get_driver(call.from_user.id)
        if not driver or driver.get('status') != 'approved':
            bot.answer_callback_query(call.id, "⛔ Siz ro'yxatda yo'qsiz!")
            return

        now = now_tashkent()

        if answer == 'yes':
            api_client.update_driver_location(call.from_user.id, None, 'finished')

            bot.edit_message_text(
                f"✅ <b>{driver['full_name']}</b>, ishingiz tugadi deb belgilandi.\n"
                f"🕐 {now}\n\nYaxshi dam oling! 🌙",
                call.message.chat.id, call.message.message_id,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "✅ Ish tugadi!")

            phone = driver.get('phone_number', '')
            phone_line = f"📞 Tel: {phone}\n" if phone else ""

            try:
                bot.send_message(
                    GROUP_CHAT_ID,
                    f"🔴 <b>{driver['full_name']}</b> bugungi ishini yakunladi.\n"
                    f"🚗 {driver['car_name']} | <code>{driver['car_number']}</code>\n"
                    f"{phone_line}"
                    f"🕐 {now}",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Guruhga xabar yuborishda xato: {e}")
        else:
            bot.edit_message_text(
                f"🚗 <b>{driver['full_name']}</b>, davom eting!\n"
                f"Keyingi tekshiruv keladi.",
                call.message.chat.id, call.message.message_id,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "Okay, davom eting!")

    # ── Haydovchilar ro'yxati ────────────────────────────────

    @bot.message_handler(func=lambda m: m.text == "👥 Haydovchilar ro'yxati")
    def drivers_list(message):
        drivers = api_client.get_approved_drivers()
        if not drivers:
            bot.send_message(message.chat.id, "📋 Haydovchilar ro'yxati bo'sh.")
            return
        text = f"👥 <b>Mahalla haydovchilari ({len(drivers)} ta):</b>\n\n"
        for i, d in enumerate(drivers, 1):
            text += (
                f"{i}. 👤 <b>{d['full_name']}</b>\n"
                f"   📞 {d['phone_number']}\n"
                f"   🚗 {d['car_name']} | <code>{d['car_number']}</code>\n\n"
            )
        bot.send_message(message.chat.id, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "🚌 Haydovchilar ma'lumoti")
    def all_drivers_info(message):
        drivers = api_client.get_approved_drivers()
        if not drivers:
            bot.send_message(message.chat.id, "📋 Hozirda tasdiqlangan haydovchilar yo'q.")
            return
        text = "🚌 <b>Mahalla liniya haydovchilari:</b>\n\n"
        for i, d in enumerate(drivers, 1):
            text += (
                f"━━━━━━━━━━━━━━━━\n"
                f"{i}. 👤 <b>{d['full_name']}</b>\n"
                f"    📞 Tel: {d['phone_number']}\n"
                f"    🚗 Rusumi: {d['car_name']}\n"
                f"    🔢 Raqami: <code>{d['car_number']}</code>\n"
            )
        text += "━━━━━━━━━━━━━━━━"
        bot.send_message(message.chat.id, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "📅 Bugungi jadval")
    def today_schedule(message):
        working = api_client.get_today_statuses(status='working')
        if not working:
            bot.send_message(message.chat.id, "📅 Bugun hali hech kim ishga chiqmagan.")
            return
        text = f"📅 <b>Bugun ishlaydigan haydovchilar ({len(working)} ta):</b>\n\n"
        for i, d in enumerate(working, 1):
            loc = f"\n    📍 {d['location']}" if d.get('location') else ""
            text += (
                f"{i}. 👤 <b>{d['driver_name']}</b>\n"
                f"    📞 {d['driver_phone']}\n"
                f"    🚙 {d['car_name']} | <code>{d['car_number']}</code>{loc}\n\n"
            )
        bot.send_message(message.chat.id, text, parse_mode='HTML')

    # ── Qayerda turish (yo'lovchi) ───────────────────────────

    @bot.message_handler(func=lambda m: m.text == "📍 Qayerda turish?")
    def where_to_wait(message):
        bot.send_message(
            message.chat.id,
            "📍 <b>Qayerda turmoqchisiz?</b>\n\nAstanovkani tanlang:",
            parse_mode='HTML',
            reply_markup=keyboards.location_choice_keyboard()
        )

    # ── Location callback ─────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith('location:'))
    def location_cb(call):
        location = call.data.split(':')[1]
        loc_name = "🏘️ Mahalla" if location == 'mahalla' else "🚏 Oydin astanovka"
        now = now_tashkent()

        driver = middlewares.get_driver(call.from_user.id)

        if driver and driver.get('status') == 'approved':
            # Haydovchi — o'z joylashuvini belgilaydi
            api_client.update_driver_location(call.from_user.id, location)
            phone = driver.get('phone_number', '')
            phone_line = f"📞 Tel: {phone}\n" if phone else ""

            try:
                bot.send_message(
                    GROUP_CHAT_ID,
                    f"📍 <b>{driver['full_name']}</b> ({driver['car_name']} | <code>{driver['car_number']}</code>)\n"
                    f"{phone_line}"
                    f"{loc_name} da turibdi! ✅\n"
                    f"🕐 {now}",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Guruhga xabar yuborishda xato: {e}")

            bot.answer_callback_query(call.id, f"✅ {loc_name} deb belgilandi!")
            bot.send_message(
                call.message.chat.id,
                f"✅ Joylashuvingiz <b>{loc_name}</b> deb saqlandi va guruhga yuborildi.\n🕐 {now}",
                parse_mode='HTML'
            )
        else:
            # Yo'lovchi — o'sha joyda kim borligini ko'radi
            statuses = api_client.get_today_statuses(status='working', location=location)
            if not statuses:
                text = f"{loc_name} da hozir hech qanday haydovchi yo'q.\n🕐 {now}"
            else:
                text = f"{loc_name} da turgan haydovchilar:\n🕐 {now}\n\n"
                for d in statuses:
                    text += (
                        f"🚗 <b>{d['driver_name']}</b> | {d['car_name']} | "
                        f"<code>{d['car_number']}</code>\n"
                        f"📞 {d['driver_phone']}\n\n"
                    )
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, text, parse_mode='HTML')

    # ── Haydovchi joylashuvini yangilash ─────────────────────

    @bot.message_handler(func=lambda m: m.text == "📍 Joylashuvni yangilash")
    def update_location_menu(message):
        if not middlewares.is_approved_driver(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Bu funksiya faqat tasdiqlangan haydovchilar uchun.")
            return
        bot.send_message(
            message.chat.id,
            "📍 <b>Joylashuvingizni tanlang:</b>",
            parse_mode='HTML',
            reply_markup=keyboards.driver_location_keyboard()
        )

    @bot.message_handler(func=lambda m: m.text == "🚗 Mahalladan ketdim")
    def moving_from_mahalla(message):
        if not middlewares.is_approved_driver(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Ruxsat yo'q.")
            return
        driver = middlewares.get_driver(message.from_user.id)
        api_client.update_driver_location(message.from_user.id, 'mahalla', 'mahalla_to_oydin')
        now = now_tashkent()
        phone = driver.get('phone_number', '') if driver else ''
        phone_line = f"📞 Tel: {phone}\n" if phone else ""
        try:
            bot.send_message(
                GROUP_CHAT_ID,
                f"🚗 <b>{driver['full_name']}</b> ({driver['car_name']} | <code>{driver['car_number']}</code>)\n"
                f"{phone_line}"
                f"Mahalladan Oydin tomon harakatlanishni boshladi! 🚏\n"
                f"🕐 {now}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Guruhga xabar yuborishda xato: {e}")
        bot.send_message(message.chat.id, f"✅ Guruhga xabar yuborildi!\n🕐 {now}")

    @bot.message_handler(func=lambda m: m.text == "🏁 Oydin tomonga ketdim")
    def moving_to_oydin(message):
        if not middlewares.is_approved_driver(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Ruxsat yo'q.")
            return
        driver = middlewares.get_driver(message.from_user.id)
        api_client.update_driver_location(message.from_user.id, 'oydin', 'mahalla_to_oydin')
        now = now_tashkent()
        phone = driver.get('phone_number', '') if driver else ''
        phone_line = f"📞 Tel: {phone}\n" if phone else ""
        try:
            bot.send_message(
                GROUP_CHAT_ID,
                f"🚗 <b>{driver['full_name']}</b> ({driver['car_name']} | <code>{driver['car_number']}</code>)\n"
                f"{phone_line}"
                f"Mahallaning oxirgi astanovkasidan Oydin tomon yo'lga chiqdi! 🚏➡️\n"
                f"🕐 {now}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Guruhga xabar yuborishda xato: {e}")
        bot.send_message(message.chat.id, f"✅ Guruhga xabar yuborildi!\n🕐 {now}")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('moving:'))
    def moving_direction_cb(call):
        if not middlewares.is_approved_driver(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Ruxsat yo'q!")
            return

        direction = call.data.split(':')[1]
        driver = middlewares.get_driver(call.from_user.id)
        location_map = {'mahalla_to_oydin': 'mahalla', 'oydin_to_mahalla': 'oydin'}
        location = location_map.get(direction, 'mahalla')
        api_client.update_driver_location(call.from_user.id, location, direction)

        direction_texts = {
            'mahalla_to_oydin': "🚗 Mahalladan Oydin tomon yo'lga chiqdi!",
            'oydin_to_mahalla': "↩️ Oydindan Mahalla tomon qaytmoqda!",
        }
        text = direction_texts.get(direction, "Joylashuv yangilandi")
        now = now_tashkent()
        phone = driver.get('phone_number', '') if driver else ''
        phone_line = f"📞 Tel: {phone}\n" if phone else ""

        try:
            bot.send_message(
                GROUP_CHAT_ID,
                f"📍 <b>{driver['full_name']}</b> ({driver['car_name']} | <code>{driver['car_number']}</code>)\n"
                f"{phone_line}"
                f"{text}\n🕐 {now}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Guruhga xabar yuborishda xato: {e}")

        bot.answer_callback_query(call.id, "✅ Guruhga xabar yuborildi!")
        bot.send_message(call.message.chat.id,
                         f"✅ Harakatlanish holati yangilandi va guruhga yuborildi!\n🕐 {now}")

        try:
            from websocket_server import ws_server
            ws_server.broadcast({
                "event": "location_update",
                "telegram_id": call.from_user.id,
                "driver_id": driver.get('id'),
                "driver_name": driver.get('full_name'),
                "phone_number": phone,
                "car_name": driver.get('car_name'),
                "car_number": driver.get('car_number'),
                "location": location,
                "moving_direction": direction,
                "timestamp": now
            })
        except Exception:
            pass

    # ── Vaqt oralig'idagi so'rov (loc_prompt) ──────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith('loc_prompt:'))
    def loc_prompt_cb(call):
        action = call.data.split(':', 1)[1]
        uid = call.from_user.id
        driver = middlewares.get_driver(uid)

        if not driver or driver.get('status') != 'approved':
            bot.answer_callback_query(call.id, "⛔ Siz tasdiqlangan haydovchi emassiz.")
            return

        now = now_tashkent()
        driver_name = driver.get('full_name', 'Haydovchi')
        car_info = f"{driver.get('car_name', '')} | <code>{driver.get('car_number', '')}</code>"
        phone = driver.get('phone_number', '')
        phone_line = f"📞 Tel: {phone}\n" if phone else ""

        if action == 'mahalla':
            api_client.update_driver_location(uid, 'mahalla')
            loc_title = "🏘️ Mahallada (astanovkada)"
            group_msg = f"📍 <b>{driver_name}</b> ({car_info})\n{phone_line}Mahalladagi astanovkada turibdi! ✅\n🕐 {now}"
            ws_loc = "mahalla"
            ws_dir = None
        elif action == 'oydin':
            api_client.update_driver_location(uid, 'oydin')
            loc_title = "🚏 Oydin astanovka"
            group_msg = f"📍 <b>{driver_name}</b> ({car_info})\n{phone_line}Oydin astanovkada turibdi! ✅\n🕐 {now}"
            ws_loc = "oydin"
            ws_dir = None
        elif action == 'moving_mahalla':
            api_client.update_driver_location(uid, 'mahalla', 'mahalla_to_oydin')
            loc_title = "🚗 Mahalladan Oydin tomon yo'lda"
            group_msg = f"🚗 <b>{driver_name}</b> ({car_info})\n{phone_line}Mahalladan Oydin tomon yo'lga chiqdi! 🚏\n🕐 {now}"
            ws_loc = "mahalla"
            ws_dir = "mahalla_to_oydin"
        elif action == 'moving_oydin':
            api_client.update_driver_location(uid, 'oydin', 'oydin_to_mahalla')
            loc_title = "↩️ Oydindan Mahalla tomon yo'lda"
            group_msg = f"↩️ <b>{driver_name}</b> ({car_info})\n{phone_line}Oydindan Mahalla tomon qaytmoqda! 🏘️\n🕐 {now}"
            ws_loc = "oydin"
            ws_dir = "oydin_to_mahalla"
        elif action == 'pause':
            api_client.set_daily_status(uid, 'working', location='Tanaffus')
            loc_title = "⏸️ Tanaffusda"
            group_msg = f"⏸️ <b>{driver_name}</b> ({car_info})\n{phone_line}Qisqa tanaffusga chiqdi.\n🕐 {now}"
            ws_loc = "tanaffus"
            ws_dir = None
        else:
            bot.answer_callback_query(call.id, "Noma'lum amal.")
            return

        bot.answer_callback_query(call.id, f"✅ Qabul qilindi: {loc_title}")

        try:
            bot.edit_message_text(
                f"✅ <b>Joylashuvingiz qabul qilindi:</b> {loc_title}\n"
                f"🕐 {now}\n\n"
                f"<i>Rahmat! Harakatingiz xavfsiz bo'lsin.</i>",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
        except Exception:
            pass

        try:
            bot.send_message(GROUP_CHAT_ID, group_msg, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Guruhga joylashuv xabarini yuborishda xato: {e}")

        try:
            from websocket_server import ws_server
            ws_server.broadcast({
                "event": "location_update",
                "telegram_id": uid,
                "driver_id": driver.get('id'),
                "driver_name": driver_name,
                "phone_number": phone,
                "car_name": driver.get('car_name'),
                "car_number": driver.get('car_number'),
                "location": ws_loc,
                "moving_direction": ws_dir,
                "location_title": loc_title,
                "timestamp": now
            })
        except Exception as e:
            logger.debug(f"WS broadcast xatosi: {e}")

    # ── Asosiy menyu ─────────────────────────────────────────

    @bot.message_handler(func=lambda m: m.text == "🔙 Asosiy menyu")
    def back_to_main(message):
        bot.send_message(message.chat.id, "🏠 Asosiy menyu",
                         reply_markup=keyboards.main_menu_keyboard())


def register_myinfo_and_lastseen(bot: telebot.TeleBot):
    """
    /myinfo — haydovchi o'z ma'lumotlarini ko'radi va tahrirlaydi
    last_seen — har bir xabarda yangilanadi (middlewares orqali)
    Bu funksiya register_driver_handlers dan KEYIN chaqiriladi
    """

    # Tahrirlash holati
    edit_states = {}

    @bot.message_handler(commands=['myinfo'])
    def cmd_myinfo(message):
        import middlewares
        driver = middlewares.get_driver(message.from_user.id)
        if not driver:
            bot.send_message(message.chat.id,
                             "❌ Siz ro'yxatda yo'qsiz. /driver buyrug'i orqali ro'yxatdan o'ting.")
            return
        if driver.get('status') != 'approved':
            bot.send_message(message.chat.id, "⏳ Profilingiz hali tasdiqlanmagan.")
            return

        _send_myinfo(bot, message.chat.id, driver)

    def _send_myinfo(bot, chat_id, driver):
        from scheduler import now_tashkent
        last_seen = driver.get('last_seen') or "ma'lumot yo'q"

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("✏️ Telefon raqamni o'zgartirish", callback_data="edit:phone"),
            types.InlineKeyboardButton("✏️ Mashina nomini o'zgartirish",  callback_data="edit:car_name"),
            types.InlineKeyboardButton("✏️ Mashina raqamini o'zgartirish", callback_data="edit:car_number"),
        )

        bot.send_message(
            chat_id,
            f"👤 <b>Mening profilim</b>\n\n"
            f"Ism: <b>{driver['full_name']}</b>\n"
            f"📞 Telefon: <b>{driver['phone_number']}</b>\n"
            f"🚗 Mashina: <b>{driver['car_name']}</b>\n"
            f"🔢 Raqam: <b>{driver['car_number']}</b>\n"
            f"🟢 Status: <b>{driver.get('status_display', '')}</b>\n"
            f"🕐 Oxirgi faollik: <b>{last_seen}</b>",
            parse_mode='HTML',
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith('edit:'))
    def edit_field_cb(call):
        import middlewares
        driver = middlewares.get_driver(call.from_user.id)
        if not driver or driver.get('status') != 'approved':
            bot.answer_callback_query(call.id, "⛔ Ruxsat yo'q!")
            return

        field = call.data.split(':')[1]
        field_names = {
            'phone':      "📞 Yangi telefon raqamni kiriting (+998XXXXXXXXX):",
            'car_name':   "🚗 Yangi mashina nomini kiriting:",
            'car_number': "🔢 Yangi mashina raqamini kiriting:",
        }

        edit_states[call.from_user.id] = field
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, field_names[field],
                         reply_markup=keyboards.cancel_keyboard())

    @bot.message_handler(func=lambda m: m.from_user.id in edit_states)
    def process_edit(message):
        if message.text == "❌ Bekor qilish":
            edit_states.pop(message.from_user.id, None)
            bot.send_message(message.chat.id, "❌ Bekor qilindi.",
                             reply_markup=keyboards.driver_menu_keyboard())
            return

        import middlewares
        field = edit_states.pop(message.from_user.id)
        field_map = {
            'phone':      'phone_number',
            'car_name':   'car_name',
            'car_number': 'car_number',
        }
        api_field = field_map[field]
        value = message.text.strip()
        if api_field == 'car_number':
            value = value.upper()

        result = api_client.update_driver_info(message.from_user.id, {api_field: value})

        if result:
            bot.send_message(message.chat.id,
                             f"✅ Ma'lumot yangilandi!",
                             reply_markup=keyboards.driver_menu_keyboard())
            driver = middlewares.get_driver(message.from_user.id)
            if driver:
                _send_myinfo(bot, message.chat.id, driver)
        else:
            bot.send_message(message.chat.id,
                             "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
                             reply_markup=keyboards.driver_menu_keyboard())