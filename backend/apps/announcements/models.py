from django.db import models


class Announcement(models.Model):
    text = models.TextField(verbose_name='Elon matni')
    sent_by = models.BigIntegerField(verbose_name='Yuboruvchi Telegram ID')
    sent_at = models.DateTimeField(auto_now_add=True)
    recipients_count = models.IntegerField(default=0, verbose_name='Qabul qiluvchilar soni')

    class Meta:
        verbose_name = 'Elon'
        verbose_name_plural = 'Elonlar'
        ordering = ['-sent_at']

    def __str__(self):
        return f"Elon {self.id} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"
