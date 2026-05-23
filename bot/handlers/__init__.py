from handlers.start import register_start_handlers
from handlers.admin import register_admin_handlers
from handlers.driver import register_driver_handlers, register_myinfo_and_lastseen
from handlers.group import register_group_handlers

def register_all_handlers(bot):
    register_start_handlers(bot)
    register_admin_handlers(bot)
    register_driver_handlers(bot)
    register_myinfo_and_lastseen(bot)
    register_group_handlers(bot)