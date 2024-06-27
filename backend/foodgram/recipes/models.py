"""
Модуль моделей для рецептов и связанных с ними данных.

В этом модуле определены модели для тегов, пользователей,
рецептов, избранного, подписок и списка покупок.
"""
from django.core.validators import (
    MaxLengthValidator, MinValueValidator,
    RegexValidator, FileExtensionValidator
)

from django.db import models
from PIL import Image

from users.models import CustomUser


TAG_MAX_LENGTH = 255
INGREDIENT_MAX_UNITS = 255
RECIPE_MAX_TEXT_LENGTH = 1000


class Tag(models.Model):
    """
    Модель тега.

    Это модель для тегов рецептов.
    """

    name = models.CharField(
        verbose_name='Тэг',
        max_length=TAG_MAX_LENGTH,
        validators=[
            MaxLengthValidator(
                TAG_MAX_LENGTH, f'Тэг не может быть больше {TAG_MAX_LENGTH}'
            ),
            RegexValidator(
                regex=r'^[a-zA-Z0-9]+$',
                message='Тэг может содержать только буквы и цифры',
                code='invalid'
            )
        ],
        unique=True,
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=15,
        unique=True,
    )
    slug = models.CharField(
        verbose_name='слаг',
        max_length=255,
        unique=True,
    )

    class Meta:
        """Мета-класс модели тэга."""

        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self) -> str:
        """
        Строковое представление тега.

        return: строка с именем тега и его цветом
        """
        return f'{self.name}: (цвет-{self.color})'


class Ingredient(models.Model):
    """
    Модель ингредиента.

    Это модель для ингредиентов рецептов.
    """

    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=255,
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=INGREDIENT_MAX_UNITS,
    )

    class Meta:
        """Мета-класс модели ингредиента."""

        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self) -> str:
        """
        Строковое представление ингредиента.

        return: строка с именем ингредиента и его единицами измерения
        """
        return f'{self.name}: {self.measurement_unit}'


class Recipe(models.Model):
    """
    Модель рецепта.

    Это модель для рецептов.
    """

    name = models.CharField(
        verbose_name='Рецепт',
        max_length=255
    )
    author = models.ForeignKey(
        verbose_name='Автор',
        related_name='recipes',
        to=CustomUser,
        on_delete=models.CASCADE
    )
    tags = models.ManyToManyField(
        verbose_name='Теги',
        to=Tag,
    )
    ingredients = models.ManyToManyField(
        verbose_name='Ингредиенты',
        to=Ingredient,
        through='RecipeIngredient',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        editable=False,
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipe_images/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['png', 'jpg', 'jpeg'])
        ]
    )
    text = models.TextField(
        verbose_name='Описание',
        max_length=RECIPE_MAX_TEXT_LENGTH,
    )
    cooking_time = models.FloatField(
        verbose_name='Время приготовления',
        default=0
    )

    class Meta:
        """Мета-класс модели рецепта."""

        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self) -> str:
        """
        Строковое представление рецепта.

        return: строка с именем рецепта и его автором
        """
        return f'{self.name}: {self.author.name}'

    def save(self, *args, **kwargs):
        """
        Сохранение рецепта.

        args: аргументы
        kwargs: именованные аргументы
        """
        super().save(*args, **kwargs)
        if self.image:
            image = Image.open(self.image)
            image.save(self.image.path)


class RecipeIngredient(models.Model):
    """Модель ингредиентов-рецепта."""

    ingredients = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        related_name='ingredients_list', verbose_name='Ингредиенты'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='recipes_ingredients_list', verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        default=0.1, validators=[MinValueValidator(1)],
        verbose_name='Количество ингредиентов'
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=INGREDIENT_MAX_UNITS,
    )

    class Meta:
        """Мета-класс модели ингредиента-рецепта."""

        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'


class Favorites(models.Model):
    """Модель избранного рецепта."""

    recipe = models.ForeignKey(
        verbose_name='Понравившиеся рецепты',
        related_name='in_favorites',
        to=Recipe,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        verbose_name='Пользователь',
        related_name='favorites',
        to=CustomUser,
        on_delete=models.CASCADE,
    )
    date_added = models.DateTimeField(
        verbose_name='Дата добавления', auto_now_add=True, editable=False
    )

    class Meta:
        """Мета-класс модели избранных рецептов."""

        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'recipe',
                    'user',
                ),
                name='Рецепт уже добавлен в избранное',
            ),
        )

    def __str__(self) -> str:
        """
        Строковое представление избранного рецепта.

        return: строка с именем пользователя и его избранным рецептом
        """
        return f'{self.user}: {self.recipe}'


class ShoppingList(models.Model):
    """
    Модель списка покупок.

    Это модель для списков покупок.
    """

    recipe = models.ForeignKey(
        verbose_name='Рецепты в списке покупок',
        related_name='carts',
        to=Recipe,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        verbose_name='Владелец списка',
        related_name='carts',
        to=CustomUser,
        on_delete=models.CASCADE,
    )
    date_added = models.DateTimeField(
        verbose_name='Дата добавления', auto_now_add=True, editable=False
    )

    class Meta:
        """Мета-класс модели списка покупок."""

        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'

    def __str__(self) -> str:
        """
        Строковое представление рецепта в списке покупок.

        return: строка с именем пользователя и его рецептом в списке покупок
        """
        return f'{self.user}: {self.recipe}'
