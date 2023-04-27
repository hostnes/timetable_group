from django.db import models


class User(models.Model):
    first_name = models.TextField(verbose_name='имя', max_length=1000, blank=True)
    telegram_id = models.CharField(verbose_name='телеграм айди', max_length=20)
    group_number = models.CharField(verbose_name='номер группы', blank=True, max_length=5)
    is_sender = models.BooleanField(verbose_name='Рассылка', default=False)

    def __str__(self):
        return f"{self.first_name} | {self.telegram_id} | {self.group_number} | {self.is_sender}"

