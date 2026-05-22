import logging
import pytz
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

TASHKENT_TZ = pytz.timezone('Asia/Tashkent')


def now_tashkent() -> str:
    """Hozirgi Toshkent vaqti — xabarlarda ko'rsatish uchun"""
    return datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y %H:%M')


def today_tashkent() -> str:
    return datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y')


# ─────────────────────────────────────────
# ERTALAB 05:00 — haydovchilarga so'rov
# ─────────────────────────────────────────
def send_morning_checkin(bot):
    import api_client
    import keyboards

    logger.info("⏰ 05:00 — Ertalabki so'rovlar yuborilmoqda...")
    drivers = api_client.get_approved_drivers()

    if not drivers:
        logger.info("Tasdiqlangan haydovchilar yo'q.")
        return

    for driver in drivers:
        try:
            bot.send_message(
                driver['telegram_id'],
                f"🌅 <b>Xayrli tong, {driver['full_name']}!</b>\n\n"
                f"🚗 {driver['car_name']} | {driver['car_number']}\n\n"
                f"📅 {today_tashkent()}\n\n"
                f"Bugun ishga chiqasizmi?",
                parse_mode='HTML',
                reply_markup=keyboards.daily_checkin_keyboard()
            )
            logger.info(f"  ✓ {driver['full_name']} ga yuborildi")
        except Exception as e:
            logger.warning(f"  ✗ {driver['telegram_id']} ga xato: {e}")

    logger.info(f"Ertalabki so'rov {len(drivers)} ta haydovchiga yuborildi.")


# ─────────────────────────────────────────
# ERTALAB 05:15 — guruhga kunlik ro'yxat
# ─────────────────────────────────────────
def send_daily_report(bot):
    import api_client
    from config import GROUP_CHAT_ID

    logger.info("⏰ 05:15 — Kunlik hisobot guruhga yuborilmoqda...")

    # Hali javob bermaganlarni "not_working" ga o'tkazamiz
    approved = api_client.get_approved_drivers()
    working_ids = set()
    today_statuses = api_client.get_today_statuses()
    for s in today_statuses:
        if s['status'] in ('working', 'not_working'):
            working_ids.add(s['driver'])

    for driver in approved:
        if driver['id'] not in working_ids:
            # Javob bermagan → not_working
            api_client.set_daily_status(driver['telegram_id'], 'not_working')
            logger.info(f"  → {driver['full_name']} javob bermadi, not_working qilindi")

    # Yangi ro'yxatni olish
    working_drivers = api_client.get_today_statuses(status='working')
    today = today_tashkent()

    if not working_drivers:
        text = (
            f"📅 <b>{today} — Bugungi ish ro'yxati</b>\n\n"
            f"Bugun hech kim ishga chiqmadi."
        )
    else:
        text = f"📅 <b>{today} — Bugun ishlaydigan haydovchilar:</b>\n\n"
        for i, d in enumerate(working_drivers, 1):
            text += (
                f"{i}. 🚗 <b>{d['driver_name']}</b>\n"
                f"   📞 {d['driver_phone']}\n"
                f"   🚙 {d['car_name']} | <code>{d['car_number']}</code>\n\n"
            )
        text += f"<i>Jami: {len(working_drivers)} ta haydovchi</i>"

    try:
        bot.send_message(GROUP_CHAT_ID, text, parse_mode='HTML')
        logger.info("Kunlik hisobot guruhga yuborildi.")
    except Exception as e:
        logger.error(f"Guruhga hisobot yuborishda xato: {e}")


# ─────────────────────────────────────────
# KECHKI 20:00 / 20:30 / 21:00
# ─────────────────────────────────────────
def send_evening_checkin(bot, slot: str):
    import api_client
    import keyboards

    logger.info(f"⏰ {slot} — Kechki so'rov yuborilmoqda...")
    working = api_client.get_today_statuses(status='working')

    if not working:
        logger.info("Bugun ishlaydigan haydovchi yo'q.")
        return

    sent = 0
    for d in working:
        # Allaqachon tugatgan bo'lsa o'tkazib yuboramiz
        if d.get('moving_direction') == 'finished':
            continue

        driver_info = api_client.get_driver_by_id(d['driver'])
        if not driver_info:
            continue

        try:
            bot.send_message(
                driver_info['telegram_id'],
                f"🌆 <b>Kechki so'rov — {slot}</b>\n"
                f"📅 {now_tashkent()}\n\n"
                f"{driver_info['full_name']}, ishingizni tugatdingizmi?",
                parse_mode='HTML',
                reply_markup=keyboards.evening_checkin_keyboard(slot)
            )
            sent += 1
        except Exception as e:
            logger.warning(f"  ✗ {driver_info['telegram_id']} ga xato: {e}")

    logger.info(f"Kechki so'rov ({slot}) {sent} ta haydovchiga yuborildi.")


# ─────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────
def setup_scheduler(bot):
    scheduler = BackgroundScheduler(timezone=TASHKENT_TZ)

    # Ertalab
    scheduler.add_job(send_morning_checkin, 'cron', hour=5, minute=0,
                      args=[bot], id='morning_checkin')
    scheduler.add_job(send_daily_report, 'cron', hour=5, minute=15,
                      args=[bot], id='daily_report')

    # Kechki
    scheduler.add_job(send_evening_checkin, 'cron', hour=20, minute=0,
                      args=[bot, '20:00'], id='evening_2000')
    scheduler.add_job(send_evening_checkin, 'cron', hour=20, minute=30,
                      args=[bot, '20:30'], id='evening_2030')
    scheduler.add_job(send_evening_checkin, 'cron', hour=21, minute=0,
                      args=[bot, '21:00'], id='evening_2100')

    scheduler.start()
    logger.info(
        "✅ APScheduler ishga tushdi (Asia/Tashkent):\n"
        "   05:00 — Ertalabki so'rov\n"
        "   05:15 — Kunlik hisobot guruhga\n"
        "   20:00 / 20:30 / 21:00 — Kechki so'rov"
    )
    return scheduler