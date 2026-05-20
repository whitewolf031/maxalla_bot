from django.contrib import admin
from .models import Driver, DailyStatus


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone_number', 'car_name', 'car_number', 'telegram_id', 'status', 'is_active', 'created_at']
    list_filter = ['status', 'is_active']
    search_fields = ['full_name', 'phone_number', 'car_number', 'telegram_id']
    list_editable = ['status', 'is_active']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DailyStatus)
class DailyStatusAdmin(admin.ModelAdmin):
    list_display = ['driver', 'date', 'status', 'location', 'moving_direction', 'updated_at']
    list_filter = ['status', 'date', 'location']
    search_fields = ['driver__full_name', 'driver__car_number']
    ordering = ['-date', 'driver__full_name']
