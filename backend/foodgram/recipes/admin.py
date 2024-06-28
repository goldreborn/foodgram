"""
Модуль администрирования для рецептов.

В этом модуле определены классы администрирования для тегов,
ингредиентов, рецептов, избранного и списка покупок.
"""
from django.contrib import admin

from recipes import models


class RecipeIngredientInline(admin.TabularInline):
    model = models.RecipeIngredient
    extra = 1


class TagAdmin(admin.ModelAdmin):
    """Класс администрирования для тегов."""

    list_display = ('pk', 'name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    list_filter = ('name', 'color', 'slug')


class IngredientAdmin(admin.ModelAdmin):
    """Класс администрирования для ингредиентов."""

    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    """Класс администрирования для рецептов."""

    list_display = ('pk', 'name', 'author', 'favorites_amount')
    search_fields = ('name', 'author', 'ingredients')
    list_filter = ('name', 'author', 'tags')
    inlines = [RecipeIngredientInline]

    def favorites_amount(self, obj):
        """
        Метод для отображения количества добавлений в избранное.

        obj: объект рецепта
        return: количество добавлений в избранное
        """
        return obj.favorites.count()


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')


class FavoriteAdmin(admin.ModelAdmin):
    """Класс администрирования для избранного."""

    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')


class ShoppingCartAdmin(admin.ModelAdmin):
    """Класс администрирования для списка покупок."""

    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')


admin.site.register(models.Tag, TagAdmin)
admin.site.register(models.Ingredient, IngredientAdmin)
admin.site.register(models.Recipe, RecipeAdmin)
admin.site.register(models.RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(models.Favorite, FavoriteAdmin)
admin.site.register(models.ShoppingList, ShoppingCartAdmin)
