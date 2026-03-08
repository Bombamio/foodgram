from django.contrib.auth.models import AbstractUser
from django.db import models
from django.forms import ValidationError

from . import constants
from . validators import username_validator


class User(AbstractUser):
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


class Subscription(models.Model):
    """
    Промежуточная связь подписка пользователя на автора.

    Поля: `user`, `author`.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=('Пользователь'),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name=('Автор'),
    )

    class Meta:
        verbose_name = ('Подписка')
        verbose_name_plural = ('Подписки')
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription'
            ),
            models.CheckConstraint(
                condition=~models.Q(user=models.F('author')),
                name='user_not_author'
            )
        ]

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} - {self.author}'
