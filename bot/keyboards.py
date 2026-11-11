import telebot
from telebot import types

# ── Asosiy menyular ──────────────────────────────────────

def main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🚗 Haydovchi paneli"),
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
        types.KeyboardButton("📊 Bugungi holat"),
        types.KeyboardButton("⏰ Ish boshlash vaqti"),
        types.KeyboardButton("📢 Elon tarqatish"),
        types.KeyboardButton("🔙 Asosiy menyu")
    )
    return markup


# ── Inline tugmalar ───────────────────────────────────────

def driver_approval_keyboard(driver_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_driver:{driver_id}"),
        types.InlineKeyboardButton("❌ Rad etish",  callback_data=f"reject_driver:{driver_id}")
    )
    return markup


def daily_checkin_keyboard():
    """Ertalabki so'rov — Ishga chiqasizmi?"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Ha, chiqaman",    callback_data="checkin:yes"),
        types.InlineKeyboardButton("❌ Yo'q, chiqmayman", callback_data="checkin:no")
    )
    return markup


def evening_checkin_keyboard(slot: str):
    """Kechki so'rov — Ishni tugatdingizmi?
    slot format: '20:00' | '20:30' | '21:00'
    callback_data: evening:yes:20:00  yoki  evening:no:20:00
    """
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Ha, tugatdim",        callback_data=f"evening:yes:{slot}"),
        types.InlineKeyboardButton("❌ Yo'q, ishlamoqdaman", callback_data=f"evening:no:{slot}")
    )
    return markup


def my_status_actions_keyboard():
    """Mening statusim xabari tagidagi tugmalar"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🟢 Ishni boshlash",  callback_data="workshift:start"),
        types.InlineKeyboardButton("🔴 Ishni tugatish", callback_data="workshift:end")
    )
    return markup


def location_choice_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏘️ Mahalla",        callback_data="location:mahalla"),
        types.InlineKeyboardButton("🚏 Oydin astanovka", callback_data="location:oydin")
    )
    return markup


def driver_location_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚗 Mahalladan Oydin tomon ketdim",  callback_data="moving:mahalla_to_oydin"),
        types.InlineKeyboardButton("↩️ Oydindan Mahalla tomon qaytdim", callback_data="moving:oydin_to_mahalla"),
        types.InlineKeyboardButton("🏘️ Mahallada turibman",             callback_data="location:mahalla"),
        types.InlineKeyboardButton("🚏 Oydinda turibman",               callback_data="location:oydin"),
    )
    return markup


def driver_location_prompt_keyboard():
    """Vaqt oralig'ida yuboriladigan so'rov: 'Qayerdasiz yoki qaysi astanovkadasiz?'"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏘️ Mahallada",             callback_data="loc_prompt:mahalla"),
        types.InlineKeyboardButton("🚏 Oydin astanovka",        callback_data="loc_prompt:oydin"),
        types.InlineKeyboardButton("🚗 Oydin tomon yo'lda",     callback_data="loc_prompt:moving_mahalla"),
        types.InlineKeyboardButton("↩️ Mahalla tomon yo'lda",   callback_data="loc_prompt:moving_oydin"),
        types.InlineKeyboardButton("⏸️ Tanaffusdaman",          callback_data="loc_prompt:pause")
    )
    return markup


def cancel_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌ Bekor qilish"))
    return markup


def work_time_view_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✏️ Vaqtni o'zgartirish", callback_data="work_time:change")
    )
    return markup


def work_time_change_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("05:00", callback_data="work_time:set:05:00"),
        types.InlineKeyboardButton("05:30", callback_data="work_time:set:05:30"),
        types.InlineKeyboardButton("06:00", callback_data="work_time:set:06:00"),
        types.InlineKeyboardButton("06:30", callback_data="work_time:set:06:30"),
        types.InlineKeyboardButton("07:00", callback_data="work_time:set:07:00"),
        types.InlineKeyboardButton("07:30", callback_data="work_time:set:07:30")
    )
    markup.add(
        types.InlineKeyboardButton("⌨️ Boshqa vaqt kiritish", callback_data="work_time:custom")
    )
    markup.add(
        types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="work_time:cancel")
    )
    return markup