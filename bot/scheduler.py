import schedule
import time
import logging
import threading
import pytz
from datetime import datetime

logger = logging.getLogger(__name__)

TASHKENT_TZ = pytz.timezone('Asia/Tashkent')


def send_morning_checkin(bot):
    """Ertalab 5:00 - barcha tasdiqlangan haydovchilarga so'rov yuborish"""
    import api_client
    import keyboards
    
    logger.info("Ertalabki so'rovlar yuborilmoqda...")
    drivers = api_client.get_approved_drivers()
    
    for driver in drivers:
        try:
            bot.send_message(
                driver['telegram_id'],
                f"🌅 <b>Xayrli tong, {driver['full_name']}!</b>\n\n"
                f"🚗 {driver['car_name']} | {driver['car_number']}\n\n"
                f"Bugun ishga chiqasizmi?",
                parse_mode='HTML',
                reply_markup=keyboards.daily_checkin_keyboard()
            )
        except Exception as e:
            logger.warning(f"Haydovchi {driver['telegram_id']} ga so'rov yuborishda xato: {e}")
    
    logger.info(f"Ertalabki so'rov {len(drivers)} ta haydovchiga yuborildi.")


def send_daily_report(bot):
    """Ertalab 5:15 - bugungi ish ro'yxatini guruhga yuborish"""
    import api_client
    from config import GROUP_CHAT_ID
    
    logger.info("Kunlik hisobot guruhga yuborilmoqda...")
    working_drivers = api_client.get_today_statuses(status='working')
    
    today = datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y')
    
    if not working_drivers:
        text = f"📅 <b>{today} - Bugungi ish ro'yxati</b>\n\nBugun hech kim ish statusini belgilamagan."
    else:
        text = f"📅 <b>{today} - Bugun ishlaydigan haydovchilar:</b>\n\n"
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


def _run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(30)


def setup_scheduler(bot):
    """Scheduler ni sozlash va ishga tushirish"""
    schedule.every().day.at("05:00").do(send_morning_checkin, bot=bot)
    schedule.every().day.at("05:15").do(send_daily_report, bot=bot)
    
    thread = threading.Thread(target=_run_scheduler, daemon=True)
    thread.start()
    logger.info("Scheduler ishga tushdi. 05:00 - so'rov, 05:15 - hisobot.")
