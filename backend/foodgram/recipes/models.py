"""
Модуль моделей для рецептов и связанных с ними данных.

В этом модуле определены модели для тегов, пользователей,
рецептов, избранного, подписок и списка покупок.
"""
from django.core.validators import (
    MinValueValidator, RegexValidator, FileExtensionValidator
)

from django.db import models
from PIL import Image

from users.models import User


TAG_MAX_LENGTH = 32
INGREDIENT_MAX_UNITS = 255
RECIPE_MAX_TEXT_LENGTH = 1000
MIN_COOKING_TIME_IN_MINUTES = 1


class Tag(models.Model):
    """
    Модель тега.

    Это модель для тегов рецептов.
    """

    name = models.CharField(
        verbose_name='Тэг',
        max_length=TAG_MAX_LENGTH,
        unique=True,
    )
    slug = models.CharField(
        verbose_name='слаг',
        max_length=TAG_MAX_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_]+$',
                message=('Пароль может состоять только'
                         'из букв латинского алфавита и цифр'),
            )
        ]
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
        return f'{self.name}'


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
        max_length=256
    )
    author = models.ForeignKey(
        verbose_name='Автор',
        related_name='recipes',
        to=User,
        on_delete=models.CASCADE
    )
    tags = models.ManyToManyField(
        Tag,
        db_index=True,
        verbose_name='Теги',
        help_text='Выберите теги'
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
        default=0,
        validators=[
            MinValueValidator(MIN_COOKING_TIME_IN_MINUTES),
        ]
    )

    is_in_shopping_cart = models.BooleanField(default=False)
    is_favorited = models.BooleanField(default=False)

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

    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        related_name='recipeingredients', verbose_name='Ингредиенты'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='recipeingredients', verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        default=0.1, validators=[MinValueValidator(1)],
        verbose_name='Количество ингредиентов'
    )

    class Meta:
        """Мета-класс модели ингредиента-рецепта."""

        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_favorite'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user.username} добавил {self.recipe.name} в избраннное'


class ShoppingCart(models.Model):
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
        to=User,
        on_delete=models.CASCADE,
    )

    class Meta:
        """Мета-класс модели списка покупок."""

        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
