"""
Модуль сериализаторов для рецептов и связанных с ними данных.

В этом модуле определены сериализаторы для тегов, пользователей,
рецептов, избранного, подписок и списка покупок.

Сериализаторы используются для преобразования данных в формат,
подходящий для передачи по сети или хранения в базе данных.
"""
from django.core.exceptions import ValidationError
from rest_framework.serializers import (
    ModelSerializer, StringRelatedField, PrimaryKeyRelatedField
)

from recipes import models
from users import models as user_models
from utils import Base64ImageField


class TagSerializer(ModelSerializer):
    """
    Сериализатор для модели Tag.

    Используется для преобразования данных модели Tag в формат JSON.
    """

    class Meta:
        """Мета-класс сериализатора тега."""
        model = models.Tag
        fields = '__all__'
        read_only_fields = '__all__'


class IngredientSerializer(ModelSerializer):
    """
    Сериализатор для модели Ingredient.

    Используется для преобразования данных модели Ingredient в формат JSON.
    """

    class Meta:
        """Мета-класс сериализатора ингредиента."""
        model = models.Ingredient
        fields = '__all__'
        read_only_fields = ('id',)


class RecipeSerializer(ModelSerializer):
    """
    Сериализатор для модели Recipe.

    Используется для преобразования данных модели Recipe в формат JSON.
    """

    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(many=True)
    author = StringRelatedField()
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        """Мета-класс сериализатора рецепта."""
        model = models.Recipe
        fields = '__all__'

    def validate(self, data):
        """
        Метод валидации данных рецепта.

        Проверяет, что время приготовления и калорийность не отрицательны.
        """
        if data.get('cooking_time') < 0:
            raise ValidationError(
                {'cooking_time': 'Время приготовления не может быть меньше 0'}
            )
        return data

    def to_representation(self, instance):
        """
        Метод преобразования данных рецепта в формат JSON.

        Добавляет автор рецепта к представлению.
        """
        representation = super().to_representation(instance)
        representation['author'] = instance.author.username
        return representation

    def create(self, validated_data):
        """
        Метод создания нового рецепта.

        Создает новый рецепт и добавляет теги и ингредиенты к нему.
        """
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = models.Recipe.objects.create(**validated_data)

        for tag in tags:
            tag_obj, _ = models.Tag.objects.get_or_create(**tag)
            recipe.tags.add(tag_obj)

        for ingredient in ingredients:
            _new, _ = models.Ingredient.objects.get_or_create(**ingredient)
            recipe.ingredients.add(_new)

        return recipe

    def update(self, instance, validated_data):
        """
        Метод обновления существующего рецепта.

        Обновляет данные рецепта и добавляет/удаляет теги и ингредиенты.
        """
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        instance = super().update(instance, validated_data)
        instance.tags.clear()

        for tag in tags:
            tag_obj, _ = models.Tag.objects.get_or_create(**tag)
            instance.tags.add(tag_obj)
        instance.ingredients.clear()

        for ingredient in ingredients:
            _new, _ = models.Ingredient.objects.get_or_create(**ingredient)
            instance.ingredients.add(_new)

        return instance


class ShoppingListSerializer(ModelSerializer):
    """
    Сериализатор для модели ShoppingList.

    Используется для преобразования данных модели ShoppingList в формат JSON.
    """

    recipe = PrimaryKeyRelatedField(queryset=models.Recipe.objects.all())
    user = StringRelatedField()

    class Meta:
        """Мета-класс сериализатора списка покупок."""
        model = models.ShoppingList
        fields = ('id', 'recipe', 'user', 'date_added',)

    def create(self, validated_data):
        """
        Метод создания нового объекта ShoppingList.

        Проверяет, что рецепт не добавлен в список покупок ранее.
        """
        recipe = validated_data.get('recipe')
        user = validated_data.get('user')
        if models.ShoppingList.objects.filter(
            recipe=recipe, user=user
        ).exists():
            raise ValidationError('Рецепт уже добавлен в список покупок')
        return super().create(validated_data)


class SubscriptionSerializer(ModelSerializer):
    """
    Сериализатор для модели Subscription.

    Используется для преобразования данных модели Subscription в формат JSON.
    """

    user = StringRelatedField()
    author = StringRelatedField()

    class Meta:
        """Мета класс подписок."""
        model = user_models.Subscription
        fields = ('id', 'user', 'author', 'subscribed_at',)

    def validate(self, attrs):
        """
        Метод валидации данных подписки.

        Проверяет, что пользователь не подписан на автора ранее.
        """
        user = attrs.get('user')
        author = attrs.get('author')
        if user_models.Subscription.objects.filter(
            user=user, author=author
        ).exists():
            raise ValidationError('Вы уже подписаны на этого автора')
        return attrs


class FavoritesSerializer(ModelSerializer):
    """
    Сериализатор для модели Favorites.

    Используется для преобразования данных модели Favorites в формат JSON.
    """

    recipe = PrimaryKeyRelatedField(queryset=models.Recipe.objects.all())
    user = StringRelatedField()

    class Meta:
        """Мета-класс избранного."""
        model = models.Favorites
        fields = ('id', 'recipe', 'user', 'date_added',)

    def create(self, validated_data):
        """
        Метод создания нового объекта Favorites.

        Проверяет, что рецепт не добавлен в избранное ранее.
        """
        recipe = validated_data.get('recipe')
        user = validated_data.get('user')
        if models.Favorites.objects.filter(recipe=recipe, user=user).exists():
            raise ValidationError('Рецепт уже добавлен в избранное')
        return super().create(validated_data)
