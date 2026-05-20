from django.contrib import admin
from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['id', 'sent_by', 'sent_at', 'recipients_count']
    readonly_fields = ['sent_at']
