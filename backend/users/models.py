from django.contrib.auth.models import AbstractUser
from django.db import models

from . import constants
from . validators import username_validator


class MyUser(AbstractUser):
    '''Кастомная модель пользователя.'''

    email = models.EmailField('Email', unique=True)
    first_name = models.CharField(
        max_length=constants.MAX_USERNAME_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=constants.MAX_USERNAME_LENGTH,
        verbose_name='Фамилия'
    )
    username = models.CharField(
        max_length=constants.MAX_USERNAME_LENGTH,
        unique=True,
        verbose_name='Логин',
        validators=[username_validator],
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/',
        null=True,
        blank=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username
