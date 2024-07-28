from django.contrib.auth import models as dj_models
from django.db import models
from django.contrib.auth.password_validation import validate_password

MAX_USERNAME_LENGTH = 150
MAX_PASSWORD_LENGTH = 150
MAX_EMAIL_LENGTH = 254
MAX_FIRSTNAME_LENGTH = 150
MAX_SECONDNAME_LENGTH = 150


class User(dj_models.AbstractUser, dj_models.PermissionsMixin):
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True
    )
    password = models.CharField(
        max_length=MAX_PASSWORD_LENGTH,
        blank=False,
        validators=[
            validate_password
        ],
    )
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
    )
    first_name = models.CharField(
        max_length=MAX_FIRSTNAME_LENGTH
    )
    last_name = models.CharField(
        max_length=MAX_SECONDNAME_LENGTH
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    groups = models.ManyToManyField(
        dj_models.Group, related_name='custom_user_groups'
    )
    user_permissions = models.ManyToManyField(
        dj_models.Permission, related_name='custom_user_permissions'
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.username} ({self.email})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name


class Subscription(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'author')
