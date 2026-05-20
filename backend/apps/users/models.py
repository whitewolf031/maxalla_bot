from django.db import models


class BotUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True, verbose_name='Telegram ID')
    username = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    is_group = models.BooleanField(default=False, verbose_name='Guruhmi')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Bot foydalanuvchisi'
        verbose_name_plural = 'Bot foydalanuvchilari'
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''} ({self.telegram_id})"
