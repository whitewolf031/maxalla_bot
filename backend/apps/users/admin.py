from django.contrib import admin
from .models import BotUser


@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'username', 'first_name', 'last_name', 'is_group', 'is_active', 'joined_at']
    list_filter = ['is_group', 'is_active']
    search_fields = ['telegram_id', 'username', 'first_name']
