"""
Модуль администрирования для рецептов.

В этом модуле определены классы администрирования для тегов,
ингредиентов, рецептов, избранного и списка покупок.
"""
from django.conf import settings
from django.contrib import admin

from recipes import models


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    """Класс администрирования для тегов."""

    list_display = ('pk', 'name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    list_filter = ('name', 'color', 'slug')
    empty_value_display = settings.EMPTY_VALUE


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Класс администрирования для ингредиентов."""

    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = settings.EMPTY_VALUE


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Класс администрирования для рецептов."""

    list_display = ('pk', 'name', 'author', 'favorites_amount')
    search_fields = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    empty_value_display = settings.EMPTY_VALUE

    def favorites_amount(self, obj):
        """
        Метод для отображения количества добавлений в избранное.

        obj: объект рецепта
        return: количество добавлений в избранное
        """
        return obj.favorites.count()


@admin.register(models.Favorites)
class FavoriteAdmin(admin.ModelAdmin):
    """Класс администрирования для избранного."""

    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = settings.EMPTY_VALUE


@admin.register(models.ShoppingList)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Класс администрирования для списка покупок."""

    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = settings.EMPTY_VALUE
