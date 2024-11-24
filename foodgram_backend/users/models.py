from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from recipe.constants import (MAX_LENGTH_EMAIL, MAX_LENGTH_FIRST_NAME,
                              MAX_LENGTH_LAST_NAME, MAX_LENGTH_PASSWORD,
                              MAX_LENGTH_USERNAME)


class User(AbstractUser):
    """Модель юзеров."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        unique=True
    )
    username = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        validators=[
            RegexValidator(regex=r'^[\ \w.@+-]+$',
                           message='Username должен содержать только буквы, '
                           'цифры и символы .@+-'
                           )
        ]
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_NAME
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_LAST_NAME,
    )
    password = models.CharField(
        max_length=MAX_LENGTH_PASSWORD
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Юзер',
        verbose_name_plural = 'Юзеры'

    def clean(self):
        super().clean()
        if self.username == 'me':
            raise ValidationError("Вы не можете использовать 'me'!!!")

    def __str__(self):
        return self.username


class Subscriptions(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers'
    )

    class Meta:
        ordering = ('-author_id',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='subscriptions_unique')]

    def __str__(self):
        return f'Подписка {self.user} на {self.author}'
