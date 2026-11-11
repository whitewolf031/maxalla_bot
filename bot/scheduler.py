import logging
from datetime import datetime
try:
    import pytz
    TASHKENT_TZ = pytz.timezone('Asia/Tashkent')
except ImportError:
    from zoneinfo import ZoneInfo
    TASHKENT_TZ = ZoneInfo('Asia/Tashkent')

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:
    BackgroundScheduler = None

logger = logging.getLogger(__name__)

# Global instances for dynamic rescheduling
_scheduler = None
_bot = None


def now_tashkent() -> str:
    return datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y %H:%M')


def today_tashkent() -> str:
    return datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y')


# ── Ertalabki so'rov (Ishga chiqasizmi?) ─────────────────────
def send_morning_checkin(bot):
    import api_client
    import keyboards
    import bot_settings

    start_str = bot_settings.get_work_start_time_str()
    logger.info(f"⏰ {start_str} — Ertalabki so'rovlar yuborilmoqda...")
    drivers = api_client.get_approved_drivers()
    if not drivers:
        logger.info("Tasdiqlangan haydovchilar yo'q.")
        return

    for driver in drivers:
        try:
            bot.send_message(
                driver['telegram_id'],
                f"🌅 <b>Xayrli tong, {driver['full_name']}!</b>\n\n"
                f"🚗 {driver['car_name']} | {driver['car_number']}\n"
                f"📅 {today_tashkent()}\n\n"
                f"Bugun ishga chiqasizmi?",
                parse_mode='HTML',
                reply_markup=keyboards.daily_checkin_keyboard()
            )
            logger.info(f"  ✓ {driver['full_name']} ga yuborildi")
        except Exception as e:
            logger.warning(f"  ✗ {driver['telegram_id']} ga xato: {e}")

    logger.info(f"Ertalabki so'rov {len(drivers)} ta haydovchiga yuborildi.")


# ── Guruhga kunlik hisobot ──────────────────────────────────
def send_daily_report(bot):
    import api_client
    import bot_settings
    from config import GROUP_CHAT_ID

    rep_str = bot_settings.get_daily_report_time_str()
    logger.info(f"⏰ {rep_str} — Kunlik hisobot guruhga yuborilmoqda...")

    # Javob bermaganlarni not_working ga o'tkazamiz
    approved = api_client.get_approved_drivers()
    today_statuses = api_client.get_today_statuses()
    answered_ids = {s['driver'] for s in today_statuses if s['status'] in ('working', 'not_working')}

    for driver in approved:
        if driver['id'] not in answered_ids:
            api_client.set_daily_status(driver['telegram_id'], 'not_working')
            logger.info(f"  → {driver['full_name']} javob bermadi, not_working qilindi")
            try:
                bot.send_message(
                    driver['telegram_id'],
                    f"⏰ Siz soat {rep_str} gacha javob bermagansiz.\n"
                    f"Bugun <b>ishlamayapdi</b> deb belgilandi.\n"
                    f"Agar xato bo'lsa — /driver → Ishni boshlash.",
                    parse_mode='HTML'
                )
            except Exception:
                pass

    # Guruhga yuborish
    working_drivers = api_client.get_today_statuses(status='working')
    today = today_tashkent()

    if not working_drivers:
        text = (
            f"📅 <b>{today} — Bugungi ish ro'yxati</b>\n\n"
            f"Bugun hech kim ishga chiqmadi."
        )
    else:
        text = f"📅 <b>{today} — Bugun ishlaydigan haydovchilar ({len(working_drivers)} ta):</b>\n\n"
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


# ── Vaqt oralig'ida haydovchilardan joylashuv so'rash (WebSocket / Avtomat) ──
def prompt_active_drivers_location(bot) -> int:
    """
    Ishlayotgan barcha haydovchilarga vaqt oralig'ida:
    'Qayerdasiz yoki qaysi astanovkadasiz?' deb so'rov yuborish.
    """
    import api_client
    import keyboards
    from config import LOCATION_PROMPT_START_HOUR, LOCATION_PROMPT_END_HOUR

    now_dt = datetime.now(TASHKENT_TZ)
    # Faqat belgilangan soatlar oralig'ida yuboriladi
    if not (LOCATION_PROMPT_START_HOUR <= now_dt.hour <= LOCATION_PROMPT_END_HOUR):
        logger.debug(f"Hozir ish soati emas ({now_dt.hour}:00). Joylashuv so'rovi yuborilmadi.")
        return 0

    logger.info("⏰ Vaqt oralig'ida haydovchilarga joylashuv so'rovi yuborilmoqda...")
    working = api_client.get_today_statuses(status='working')
    if not working:
        logger.info("Bugun ayni damda ishlayotgan haydovchilar yo'q.")
        return 0

    sent_count = 0
    now_str = now_tashkent()

    for d in working:
        if d.get('moving_direction') == 'finished':
            continue

        driver_info = api_client.get_driver_by_id(d['driver'])
        if not driver_info or not driver_info.get('telegram_id'):
            continue

        tg_id = driver_info['telegram_id']
        driver_name = driver_info.get('full_name', 'Haydovchi')
        car_info = f"{driver_info.get('car_name', '')} | <code>{driver_info.get('car_number', '')}</code>"

        text = (
            f"📍 <b>Hurmatli {driver_name}!</b>\n\n"
            f"🚙 {car_info}\n"
            f"🕐 {now_str}\n\n"
            f"<b>Qayerdasiz yoki qaysi astanovkadasiz?</b>\n"
            f"Iltimos, hozirgi joylashuvingizni tanlang:"
        )

        try:
            bot.send_message(
                tg_id,
                text,
                parse_mode='HTML',
                reply_markup=keyboards.driver_location_prompt_keyboard()
            )
            sent_count += 1
            logger.info(f"  ✓ {driver_name} ({tg_id}) ga joylashuv so'rovi yuborildi.")
        except Exception as e:
            logger.warning(f"  ✗ {tg_id} ga joylashuv so'rovini yuborishda xato: {e}")

    logger.info(f"Joylashuv so'rovi {sent_count} ta haydovchiga yuborildi.")

    # WebSocket mijozlariga event yuborish
    try:
        from websocket_server import ws_server
        ws_server.broadcast({
            "event": "location_prompts_dispatched",
            "sent_count": sent_count,
            "timestamp": now_str
        })
    except Exception as e:
        logger.debug(f"WS broadcast xatosi: {e}")

    return sent_count


# ── 20:00 / 20:30 / 21:00 — Kechki so'rov ───────────────────
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
        if d.get('moving_direction') == 'finished':
            continue
        driver_info = api_client.get_driver_by_id(d['driver'])
        if not driver_info:
            continue
        try:
            bot.send_message(
                driver_info['telegram_id'],
                f"🌆 <b>Kechki so'rov — {slot}</b>\n"
                f"🕐 {now_tashkent()}\n\n"
                f"{driver_info['full_name']}, ishingizni tugatdingizmi?",
                parse_mode='HTML',
                reply_markup=keyboards.evening_checkin_keyboard(slot)
            )
            sent += 1
        except Exception as e:
            logger.warning(f"  ✗ {driver_info['telegram_id']} ga xato: {e}")

    logger.info(f"Kechki so'rov ({slot}) {sent} ta haydovchiga yuborildi.")


# ── 00:00 — Yarim kechada tozalash ───────────────────────────
def reset_at_midnight(bot):
    """
    Har kuni yarim kechada:
    1. location va moving_direction — None ga o'tkaziladi
    2. Ertasi kun toza boshlanadi
    """
    import api_client

    logger.info("⏰ 00:00 — Yarim kechada tozalash boshlanadi...")
    result = api_client.reset_daily_locations()
    if result:
        logger.info(f"  ✓ Tozalandi: {result.get('detail', '')}")
    else:
        logger.error("  ✗ Tozalashda xato!")


# ── Schedulerni dinamik yangilash (Admin vaqtni o'zgartirganda) ─
def update_morning_schedule(new_hour: int, new_minute: int) -> bool:
    """
    Admin ertalabki ish vaqtini o'zgartirganda,
    APScheduler joblarini to'xtatmasdan yangi vaqtga qayta sozlaydi.
    """
    global _scheduler, _bot
    if not _scheduler:
        logger.warning("Scheduler hali ishga tushirilmagan.")
        return False

    rep_total = (new_hour * 60 + new_minute + 15) % (24 * 60)
    rep_h, rep_m = rep_total // 60, rep_total % 60

    try:
        if _scheduler.get_job('morning_checkin'):
            _scheduler.reschedule_job('morning_checkin', trigger='cron', hour=new_hour, minute=new_minute)
        elif _bot:
            _scheduler.add_job(send_morning_checkin, 'cron', hour=new_hour, minute=new_minute, args=[_bot], id='morning_checkin')
        logger.info(f"✅ morning_checkin yangi vaqtga o'tkazildi: {new_hour:02d}:{new_minute:02d}")
    except Exception as e:
        logger.error(f"morning_checkin reschedule xatosi: {e}")
        return False

    try:
        if _scheduler.get_job('daily_report'):
            _scheduler.reschedule_job('daily_report', trigger='cron', hour=rep_h, minute=rep_m)
        elif _bot:
            _scheduler.add_job(send_daily_report, 'cron', hour=rep_h, minute=rep_m, args=[_bot], id='daily_report')
        logger.info(f"✅ daily_report yangi vaqtga o'tkazildi: {rep_h:02d}:{rep_m:02d}")
    except Exception as e:
        logger.error(f"daily_report reschedule xatosi: {e}")
        return False

    return True


# ── Scheduler sozlash ─────────────────────────────────────────
def setup_scheduler(bot):
    global _scheduler, _bot
    import bot_settings
    from config import LOCATION_PROMPT_INTERVAL_MINUTES

    _bot = bot
    scheduler = BackgroundScheduler(timezone=TASHKENT_TZ)
    _scheduler = scheduler

    start_h, start_m = bot_settings.get_work_start_time()
    rep_h, rep_m = bot_settings.get_daily_report_time()

    # Ertalabki so'rov
    scheduler.add_job(send_morning_checkin, 'cron', hour=start_h, minute=start_m,
                      args=[bot], id='morning_checkin')

    # Guruhga hisobot (+15 daqiqa)
    scheduler.add_job(send_daily_report, 'cron', hour=rep_h, minute=rep_m,
                      args=[bot], id='daily_report')

    # Kechki so'rovlar
    scheduler.add_job(send_evening_checkin, 'cron', hour=20, minute=0,
                      args=[bot, '20:00'], id='evening_2000')
    scheduler.add_job(send_evening_checkin, 'cron', hour=20, minute=30,
                      args=[bot, '20:30'], id='evening_2030')
    scheduler.add_job(send_evening_checkin, 'cron', hour=21, minute=0,
                      args=[bot, '21:00'], id='evening_2100')

    # Yarim kechada tozalash
    scheduler.add_job(reset_at_midnight, 'cron', hour=0, minute=0,
                      args=[bot], id='midnight_reset')

    # Vaqt oralig'ida haydovchilarga joylashuv so'rovini yuborish
    scheduler.add_job(prompt_active_drivers_location, 'interval',
                      minutes=LOCATION_PROMPT_INTERVAL_MINUTES,
                      args=[bot], id='location_prompts')

    scheduler.start()

    start_str = f"{start_h:02d}:{start_m:02d}"
    rep_str = f"{rep_h:02d}:{rep_m:02d}"

    logger.info(
        f"✅ APScheduler ishga tushdi (Asia/Tashkent):\n"
        f"   {start_str} — Ertalabki so'rov (Ishga chiqasizmi?)\n"
        f"   {rep_str} — Kunlik hisobot guruhga\n"
        f"   Har {LOCATION_PROMPT_INTERVAL_MINUTES} daqiqada — Haydovchilarga 'Qayerdasiz?' so'rovi\n"
        f"   20:00 / 20:30 / 21:00 — Kechki so'rov\n"
        f"   00:00 — Yarim kechada tozalash"
    )
    return scheduler