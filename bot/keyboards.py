import telebot
from telebot import types


# ---- Asosiy menyular ----

def main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🚌 Haydovchilar ma'lumoti"),
        types.KeyboardButton("📍 Qayerda turish?"),
        types.KeyboardButton("📅 Bugungi jadval"),
        types.KeyboardButton("ℹ️ Bot haqida")
    )
    return markup


def driver_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 Mening statusim"),
        types.KeyboardButton("📍 Joylashuvni yangilash"),
        types.KeyboardButton("🚗 Mahalladan ketdim"),
        types.KeyboardButton("🏁 Oydin tomonga ketdim"),
        types.KeyboardButton("👥 Haydovchilar ro'yxati"),
        types.KeyboardButton("🔙 Asosiy menyu")
    )
    return markup


def admin_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📋 Kutayotgan so'rovlar"),
        types.KeyboardButton("✅ Tasdiqlangan haydovchilar"),
        types.KeyboardButton("📢 Elon tarqatish"),
        types.KeyboardButton("📊 Bugungi holat"),
        types.KeyboardButton("🔙 Asosiy menyu")
    )
    return markup


# ---- Inline tugmalar ----

def driver_approval_keyboard(driver_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_driver:{driver_id}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_driver:{driver_id}")
    )
    return markup


def daily_checkin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Ha, ishga chiqaman", callback_data="checkin:yes"),
        types.InlineKeyboardButton("❌ Yo'q, ishlamayapman", callback_data="checkin:no")
    )
    return markup


def evening_checkin_keyboard(slot: str):
    """Kechki 'ishni tugatdingizmi?' tugmalari"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Ha, tugatdim", callback_data=f"evening:yes:{slot}"),
        types.InlineKeyboardButton("❌ Yo'q, hali ishlamoqdaman", callback_data=f"evening:no:{slot}")
    )
    return markup


def location_choice_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏘️ Mahalla", callback_data="location:mahalla"),
        types.InlineKeyboardButton("🚏 Oydin astanovka", callback_data="location:oydin")
    )
    return markup


def driver_location_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚗 Mahalladan Oydin tomon yurib ketdim", callback_data="moving:mahalla_to_oydin"),
        types.InlineKeyboardButton("↩️ Oydindan Mahalla tomon qaytdim", callback_data="moving:oydin_to_mahalla"),
        types.InlineKeyboardButton("🏘️ Mahallada turibman", callback_data="location:mahalla"),
        types.InlineKeyboardButton("🚏 Oydinda turibman", callback_data="location:oydin"),
    )
    return markup


def cancel_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌ Bekor qilish"))
    return markup