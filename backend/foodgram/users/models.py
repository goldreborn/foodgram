from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.contrib.auth.models import Group, Permission


MAX_LENGTH = 255
MAX_USERNAME_LENGTH = 30
MAX_FIRSTNAME_LENGTH = 30
MAX_SECONDNAME_LENGTH = 30
MAX_PHONE_LENGTH = 30
MAX_PASSWORD_LENGTH = 50
MAX_EMAIL_LENGTH = 50


class CustomUser(AbstractUser, PermissionsMixin):
    """
    Класс User - это пользовательская модель.

    Переменные:

    * username: строка, уникальное имя пользователя,
        которое может состоять только из букв латинского алфавита и цифр.
    * password: строка,
        пароль в которой может быть только из букв латинского алфавита и цифр.
    * email: строка, уникальный адрес электронной почты,
        который должен соответствовать стандартному формату электронной почты.
    * first_name: строка, имя пользователя,
        которое может состоять только из букв кириллицы.
    * last_name: строка, фамилия пользователя,
        которая может состоять только из букв кириллицы.
    * phone: строка, номер телефона пользователя,
        который должен соответствовать стандартному формату телефона.

    Методы:

    * __str__:
        возвращает строковое представлеие пользователя в формате "Имя Фамилия".
    * get_full_name:
        возвращает полное имя пользователя в формате "Имя Фамилия".
    * get_short_name:
        возвращает короткое имя пользователя, которое является именем.
    """

    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_]+$',
                message=('Имя пользователя может состоять только'
                         'из букв латинского алфавита и цифр'),
            )
        ])

    password = models.CharField(
        max_length=MAX_PASSWORD_LENGTH,
        blank=False,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_]+$',
                message=('Пароль может состоять только'
                         'из букв латинского алфавита и цифр'),
            )
        ])

    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\S+@\S+\.\S+$",
                message='Неверный email адрес',
            )
        ])

    first_name = models.CharField(
        max_length=MAX_FIRSTNAME_LENGTH,
        validators=[
            RegexValidator(
                regex=r'^[А-Яа-яЁё]+$',
                message=('Имя может состоять только'
                         'из букв кириллицы'),
            )
        ])

    last_name = models.CharField(
        max_length=MAX_SECONDNAME_LENGTH,
        validators=[
            RegexValidator(
                regex=r'^[А-Яа-яЁё]+$',
                message=('Фамилия может состоять только'
                         'из букв кириллицы'),
            )
        ])

    phone = models.CharField(
        max_length=MAX_PHONE_LENGTH,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{1,3}?[-.]?\(?(?:\d{2,3})\)?[-.]?\d\d\d[-.]?\d\d\d\d$',
                message='Неверный формат телефона',
            )
        ])

    groups = models.ManyToManyField(Group, related_name='custom_user_groups')

    user_permissions = models.ManyToManyField(
        Permission, related_name='custom_user_permissions'
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        """Мета-класс модели кастомного пользователя."""

        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        unique_together = (('first_name', 'last_name'),)

    def get_permissions(self):
        return self.user_permissions

    def __str__(self):
        """Строковое представление кастомного пользователя."""
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        """Полное имя кастомного пользователя."""
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        """Короткое имя кастомного пользователя."""
        return self.first_name


class Subscription(models.Model):
    """
    Модель подписки на авторов.

    Поля:

    * user: ссылка на пользователя, который подписался на автора
    * author: ссылка на автора, на которого подписался пользователь
    * subscribed_at: дата и время подписки

    Мета-поля:

    * verbose_name: название модели в единственном числе
    * verbose_name_plural: название модели во множественном числе
    * unique_together: уникальность пары полей user и author

    Методы:

    * __str__: возвращает строковое представление подписки
    """

    user = models.ForeignKey(
        to=CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriber'
    )
    author = models.ForeignKey(
        to=CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribed_to'
    )

    class Meta:
        """Мета-класс модели подписки."""

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'author',)

    def __str__(self):
        """Строковое представление подписки."""
        return f'{self.user.name} Подписан на {self.author.name}'
