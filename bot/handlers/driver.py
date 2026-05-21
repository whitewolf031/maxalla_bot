import telebot
import logging
import keyboards
import middlewares
import api_client
from telebot import types
from config import GROUP_CHAT_ID

logger = logging.getLogger(__name__)

# Registration state management
user_states = {}
registration_data = {}


def register_driver_handlers(bot: telebot.TeleBot):

    @bot.message_handler(commands=['driver'])
    def cmd_driver(message):
        telegram_id = message.from_user.id
        driver = middlewares.get_driver(telegram_id)

        if not driver:
            _start_registration(bot, message)
            return

        status = driver.get('status')

        if status == 'pending':
            bot.send_message(
                message.chat.id,
                "⏳ Sizning so'rovingiz hali ko'rib chiqilmagan.\n"
                "Admin tasdiqlashini kuting.",
            )
            return

        if status == 'rejected':
            bot.send_message(
                message.chat.id,
                "❌ Sizning so'rovingiz rad etilgan.\n"
                "Murojaat uchun admin bilan bog'laning."
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

    # ---- Registration ----

    def _start_registration(bot, message):
        user_id = message.from_user.id
        user_states[user_id] = 'waiting_full_name'
        registration_data[user_id] = {}

        bot.send_message(
            message.chat.id,
            "📝 <b>Haydovchi sifatida ro'yxatdan o'tish</b>\n\n"
            "To'liq ismingizni kiriting (Familiya Ism Otasining ismi):",
            parse_mode='HTML',
            reply_markup=types.ReplyKeyboardRemove()
        )

    @bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_full_name')
    def process_full_name(message):
        user_id = message.from_user.id
        registration_data[user_id]['full_name'] = message.text.strip()
        user_states[user_id] = 'waiting_phone'

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
        user_id = message.from_user.id
        phone = message.contact.phone_number
        if not phone.startswith('+'):
            phone = '+' + phone
        registration_data[user_id]['phone_number'] = phone
        user_states[user_id] = 'waiting_car_name'
        bot.send_message(message.chat.id, "🚗 Avtomobil nomini kiriting (masalan: Damas):",
                         reply_markup=types.ReplyKeyboardRemove())

    @bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_phone')
    def process_phone(message):
        user_id = message.from_user.id
        registration_data[user_id]['phone_number'] = message.text.strip()
        user_states[user_id] = 'waiting_car_name'
        bot.send_message(message.chat.id, "🚗 Avtomobil nomini kiriting (masalan: Damas):",
                         reply_markup=types.ReplyKeyboardRemove())

    @bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_car_name')
    def process_car_name(message):
        user_id = message.from_user.id
        registration_data[user_id]['car_name'] = message.text.strip()
        user_states[user_id] = 'waiting_car_number'
        bot.send_message(message.chat.id, "🔢 Avtomobil raqamini kiriting (masalan: 01 A 123 BA):")

    @bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_car_number')
    def process_car_number(message):
        user_id = message.from_user.id
        registration_data[user_id]['car_number'] = message.text.strip().upper()

        data = registration_data[user_id]

        confirm_text = (
            "✅ <b>Ma'lumotlaringizni tasdiqlang:</b>\n\n"
            f"👤 Ism: <b>{data['full_name']}</b>\n"
            f"📞 Telefon: <b>{data['phone_number']}</b>\n"
            f"🚗 Avtomobil: <b>{data['car_name']}</b>\n"
            f"🔢 Raqam: <b>{data['car_number']}</b>\n\n"
            "Yuborish uchun ✅ ni bosing:"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"reg_confirm:{user_id}"),
            types.InlineKeyboardButton("❌ Bekor", callback_data=f"reg_cancel:{user_id}")
        )

        user_states[user_id] = 'waiting_confirm'
        bot.send_message(message.chat.id, confirm_text, parse_mode='HTML', reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('reg_confirm:'))
    def confirm_registration(call):
        user_id = int(call.data.split(':')[1])

        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "Bu sizning so'rovingiz emas!")
            return

        data = registration_data.get(user_id, {})
        data['telegram_id'] = user_id
        data['telegram_username'] = call.from_user.username

        result = api_client.register_driver(data)

        if result:
            user_states.pop(user_id, None)
            registration_data.pop(user_id, None)

            bot.edit_message_text(
                "✅ So'rovingiz yuborildi!\n\n"
                "⏳ Admin ko'rib chiqadi va tasdiqlaydi.\n"
                "Tasdiqlangandan so'ng xabar olasiz.",
                call.message.chat.id,
                call.message.message_id
            )

            from config import ADMIN_IDS
            for admin_id in ADMIN_IDS:
                try:
                    notify_text = (
                        f"🆕 <b>Yangi haydovchi so'rovi!</b>\n\n"
                        f"👤 {data['full_name']}\n"
                        f"📞 {data['phone_number']}\n"
                        f"🚗 {data['car_name']} | {data['car_number']}\n"
                        f"🆔 TG: <code>{user_id}</code>"
                    )
                    bot.send_message(admin_id, notify_text, parse_mode='HTML',
                                     reply_markup=keyboards.driver_approval_keyboard(result['id']))
                except Exception:
                    pass
        else:
            bot.answer_callback_query(call.id, "Xatolik yuz berdi. Qayta urinib ko'ring.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('reg_cancel:'))
    def cancel_registration(call):
        user_id = int(call.data.split(':')[1])
        user_states.pop(user_id, None)
        registration_data.pop(user_id, None)
        bot.edit_message_text("❌ Ro'yxatdan o'tish bekor qilindi.", call.message.chat.id, call.message.message_id)

    # ---- Driver menu handlers ----

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
        location = my.get('location') or "noma'lum"
        if my:
            status_icons = {'working': '✅', 'not_working': '❌', 'pending': '⏳'}
            icon = status_icons.get(my['status'], '❓')
            loc = f"\n📍 Joylashuv: {location}" if my.get("location") else ""
            text = f"{icon} <b>Bugungi statusingiz:</b> {my['status_display']}{loc}"
        else:
            text = "⏳ Bugungi status belgilanmagan. Ertalab 5:00 da so'rov keladi."

        bot.send_message(message.chat.id, text, parse_mode='HTML')

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
            bot.send_message(message.chat.id, "📅 Bugun hali hech kim ish statusini belgilamagan.")
            return

        text = f"📅 <b>Bugun ishlaydigan haydovchilar ({len(working)} ta):</b>\n\n"
        for i, d in enumerate(working, 1):
            loc = f"\n    📍 {d.get('location', '')}" if d.get('location') else ""
            text += (
                f"{i}. 👤 <b>{d['driver_name']}</b>\n"
                f"    📞 {d['driver_phone']}\n"
                f"    🚙 {d['car_name']} | <code>{d['car_number']}</code>{loc}\n\n"
            )

        bot.send_message(message.chat.id, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "📍 Qayerda turish?")
    def where_to_wait(message):
        bot.send_message(
            message.chat.id,
            "📍 <b>Qayerda turmoqchisiz?</b>\n\nAstanovkani tanlang:",
            parse_mode='HTML',
            reply_markup=keyboards.location_choice_keyboard()
        )

    # FIX #3: location tugmasi bosilganda — DB ga saqlash + guruhga xabar
    @bot.callback_query_handler(func=lambda c: c.data.startswith('location:'))
    def location_cb(call):
        location = call.data.split(':')[1]

        # Agar haydovchi bo'lsa — o'z joylashuvini belgilaydi
        driver = middlewares.get_driver(call.from_user.id)
        if driver and driver.get('status') == 'approved':
            # DB ga saqlash
            api_client.update_driver_location(call.from_user.id, location)

            loc_name = "🏘️ Mahallada" if location == 'mahalla' else "🚏 Oydin astanovkada"

            # Guruhga xabar
            try:
                bot.send_message(
                    GROUP_CHAT_ID,
                    f"📍 <b>{driver['full_name']}</b> ({driver['car_name']} | <code>{driver['car_number']}</code>)\n"
                    f"{loc_name} turibdi! ✅",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Guruhga xabar yuborishda xato: {e}")

            bot.answer_callback_query(call.id, f"✅ {loc_name} deb belgilandi!")
            bot.send_message(
                call.message.chat.id,
                f"✅ Joylashuvingiz <b>{loc_name}</b> deb saqlandi va guruhga yuborildi.",
                parse_mode='HTML'
            )
        else:
            # Oddiy yo'lovchi — o'sha joyda kim borligini ko'radi
            statuses = api_client.get_today_statuses(status='working', location=location)
            loc_name = "🏘️ Mahalla" if location == 'mahalla' else "🚏 Oydin astanovka"

            if not statuses:
                text = f"{loc_name} da hozir hech qanday haydovchi yo'q."
            else:
                text = f"{loc_name} da turgan haydovchilar:\n\n"
                for d in statuses:
                    text += (
                        f"🚗 <b>{d['driver_name']}</b> | {d['car_name']} | "
                        f"<code>{d['car_number']}</code>\n"
                        f"📞 {d['driver_phone']}\n\n"
                    )

            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, text, parse_mode='HTML')

    # ---- Driver location updates ----

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

        try:
            bot.send_message(
                GROUP_CHAT_ID,
                f"🚗 <b>{driver['full_name']}</b> ({driver['car_name']} | <code>{driver['car_number']}</code>) "
                f"Mahalladan Oydin tomon harakatlanishni boshladi! 🚏",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Guruhga xabar yuborishda xato: {e}")

        bot.send_message(message.chat.id, "✅ Guruhga xabar yuborildi!")

    @bot.message_handler(func=lambda m: m.text == "🏁 Oydin tomonga ketdim")
    def moving_to_oydin(message):
        if not middlewares.is_approved_driver(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Ruxsat yo'q.")
            return

        driver = middlewares.get_driver(message.from_user.id)
        api_client.update_driver_location(message.from_user.id, 'oydin', 'mahalla_to_oydin')

        try:
            bot.send_message(
                GROUP_CHAT_ID,
                f"🚗 <b>{driver['full_name']}</b> ({driver['car_name']} | <code>{driver['car_number']}</code>) "
                f"Mahallaning oxirgi astanovkasidan Oydin tomon yo'lga chiqdi! 🚏➡️",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Guruhga xabar yuborishda xato: {e}")

        bot.send_message(message.chat.id, "✅ Guruhga xabar yuborildi!")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('moving:'))
    def moving_direction_cb(call):
        if not middlewares.is_approved_driver(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Ruxsat yo'q!")
            return

        direction = call.data.split(':')[1]
        driver = middlewares.get_driver(call.from_user.id)

        location_map = {
            'mahalla_to_oydin': 'mahalla',
            'oydin_to_mahalla': 'oydin',
        }
        location = location_map.get(direction, 'mahalla')
        api_client.update_driver_location(call.from_user.id, location, direction)

        direction_texts = {
            'mahalla_to_oydin': "🚗 Mahalladan Oydin tomon yo'lga chiqdi!",
            'oydin_to_mahalla': "↩️ Oydindan Mahalla tomon qaytmoqda!",
        }
        text = direction_texts.get(direction, "Joylashuv yangilandi")

        try:
            bot.send_message(
                GROUP_CHAT_ID,
                f"📍 <b>{driver['full_name']}</b> ({driver['car_name']} | <code>{driver['car_number']}</code>)\n{text}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Guruhga xabar yuborishda xato: {e}")

        bot.answer_callback_query(call.id, "✅ Guruhga xabar yuborildi!")
        bot.send_message(call.message.chat.id, "✅ Harakatlanish holati yangilandi va guruhga yuborildi!")

    # ---- Daily check-in callbacks ----

    @bot.callback_query_handler(func=lambda c: c.data.startswith('checkin:'))
    def daily_checkin_cb(call):
        answer = call.data.split(':')[1]

        driver = middlewares.get_driver(call.from_user.id)
        if not driver or driver.get('status') != 'approved':
            bot.answer_callback_query(call.id, "⛔ Siz ro'yxatda yo'qsiz!")
            return

        if answer == 'yes':
            api_client.set_daily_status(call.from_user.id, 'working')
            bot.edit_message_text(
                f"✅ <b>{driver['full_name']}</b>, bugun ish ro'yxatiga qo'shildingiz!\n"
                f"🚗 {driver['car_name']} | {driver['car_number']}",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "✅ Ro'yxatga qo'shildingiz!")
        else:
            api_client.set_daily_status(call.from_user.id, 'not_working')
            bot.edit_message_text(
                f"❌ <b>{driver['full_name']}</b>, bugun ishlamaysiz deb belgilandi.\nDam oling! 😊",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "❌ Belgilandi.")

    # ---- Evening check-in callbacks ----

    @bot.callback_query_handler(func=lambda c: c.data.startswith('evening:'))
    def evening_checkin_cb(call):
        # format: evening:yes:20:00  yoki  evening:no:20:30
        parts = call.data.split(':')
        answer = parts[1]   # 'yes' yoki 'no'
        slot = f"{parts[2]}:{parts[3]}"  # '20:00'

        driver = middlewares.get_driver(call.from_user.id)
        if not driver or driver.get('status') != 'approved':
            bot.answer_callback_query(call.id, "⛔ Siz ro'yxatda yo'qsiz!")
            return

        if answer == 'yes':
            # 'finished' deb belgilaymiz — keyingi slotlarda xabar ketmaydi
            api_client.update_driver_location(call.from_user.id, None, 'finished')

            bot.edit_message_text(
                f"✅ <b>{driver['full_name']}</b>, ishingiz tugadi deb belgilandi.\n"
                f"Yaxshi dam oling! 🌙",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "✅ Ish tugadi!")

            try:
                bot.send_message(
                    GROUP_CHAT_ID,
                    f"🏁 <b>{driver['full_name']}</b> ({driver['car_name']} | <code>{driver['car_number']}</code>) "
                    f"bugungi ishini yakunladi. ({slot})",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Guruhga xabar yuborishda xato: {e}")

        else:
            # Hali ishlayapti — xabarni o'zgartirib qo'yamiz
            bot.edit_message_text(
                f"🚗 <b>{driver['full_name']}</b>, davom eting!\n"
                f"Keyingi tekshiruv keladi.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "Okay, davom eting!")

    @bot.message_handler(func=lambda m: m.text == "🔙 Asosiy menyu")
    def back_to_main(message):
        bot.send_message(
            message.chat.id,
            "🏠 Asosiy menyu",
            reply_markup=keyboards.main_menu_keyboard()
        )