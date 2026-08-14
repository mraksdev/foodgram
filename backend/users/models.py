from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with email as the unique login field."""

    email = models.EmailField(
        'адрес электронной почты',
        max_length=254,
        unique=True,
        blank=False,
    )
    avatar = models.ImageField(
        'аватар',
        upload_to='avatars/',
        null=True,
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta(AbstractUser.Meta):
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self) -> str:
        return self.email


class Subscription(models.Model):
    """Subscription of a user to an author."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='автор',
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription',
            ),
            models.CheckConstraint(
                condition=~models.Q(user=models.F('author')),
                name='cannot_subscribe_to_self',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user} -> {self.author}'
