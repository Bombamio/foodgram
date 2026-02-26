from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    '''Кастомная модель пользователя.'''

    avatar = models.ImageField(
        'Аватар',
        upload_to='users/',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username
