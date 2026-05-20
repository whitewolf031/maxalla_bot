from django.db import models


class Driver(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Kutilmoqda'),
        (STATUS_APPROVED, 'Tasdiqlangan'),
        (STATUS_REJECTED, 'Rad etilgan'),
    ]

    full_name = models.CharField(max_length=255, verbose_name='To\'liq ism')
    phone_number = models.CharField(max_length=20, verbose_name='Telefon raqam')
    car_name = models.CharField(max_length=100, verbose_name='Avtomobil nomi')
    car_number = models.CharField(max_length=20, verbose_name='Avtomobil raqami')
    telegram_id = models.BigIntegerField(unique=True, verbose_name='Telegram ID')
    telegram_username = models.CharField(max_length=100, blank=True, null=True, verbose_name='Telegram username')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='Status')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Qo\'shilgan vaqt')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')

    class Meta:
        verbose_name = 'Haydovchi'
        verbose_name_plural = 'Haydovchilar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.car_number}"


class DailyStatus(models.Model):
    STATUS_WORKING = 'working'
    STATUS_NOT_WORKING = 'not_working'
    STATUS_PENDING = 'pending'

    STATUS_CHOICES = [
        (STATUS_WORKING, 'Ishlamoqda'),
        (STATUS_NOT_WORKING, 'Ishlamayapti'),
        (STATUS_PENDING, 'Javob bermagan'),
    ]

    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='daily_statuses', verbose_name='Haydovchi')
    date = models.DateField(verbose_name='Sana')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='Status')
    location = models.CharField(max_length=50, blank=True, null=True, verbose_name='Joylashuv', 
                                 help_text='mahalla yoki oydin')
    moving_direction = models.CharField(max_length=50, blank=True, null=True, verbose_name='Harakat yo\'nalishi')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Kunlik status'
        verbose_name_plural = 'Kunlik statuslar'
        unique_together = ['driver', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.driver.full_name} - {self.date} - {self.get_status_display()}"
