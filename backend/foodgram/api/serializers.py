"""
Модуль сериализаторов для рецептов и связанных с ними данных.

В этом модуле определены сериализаторы для тегов, пользователей,
рецептов, избранного, подписок и списка покупок.

Сериализаторы используются для преобразования данных в формат,
подходящий для передачи по сети или хранения в базе данных.
"""
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db.transaction import atomic
from djoser import serializers as djoser_serializers
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes import models
from .utils import Base64ImageField
from users.models import User, Subscription


class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    """Сериализатор для регистрации пользователей."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )


class UserSerializer(djoser_serializers.UserSerializer):
    """Сериализатор для работы с информацией о пользователях."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar',
        )

    def update(self, instance, validated_data):
        if 'avatar' in validated_data:
            instance.avatar = validated_data['avatar']
        return super().update(instance, validated_data)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated and Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        )


class UserSubscribeRepresentSerializer(UserSerializer):
    """Сериализатор для предоставления информации о подписках пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = (
            'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeMiniSerializer(
            recipes, many=True, context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class UserSubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки/отписки от пользователей."""
    class Meta:
        model = Subscription
        fields = '__all__'
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя'
            )
        ]

    def validate(self, data):
        request = self.context.get('request')
        if request.user == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя.'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return UserSubscribeRepresentSerializer(
            instance.author, context={'request': request}
        ).data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами."""
    class Meta:
        model = models.Ingredient
        fields = '__all__'


class IngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения информации об ингредиентах."""
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = models.RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientPostSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = models.RecipeIngredient
        fields = ('id', 'amount')


class RecipeMiniSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с краткой информацией о рецепте."""
    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""
    class Meta:
        model = models.Tag
        fields = '__all__'


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientPostSerializer(
        many=True, source='recipeingredient_set'
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=models.Tag.objects.all()
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = models.Recipe
        fields = (
            'name', 'text', 'cooking_time', 'image', 'tags', 'ingredients'
        )

    def validate(self, data):
        if data.get('cooking_time') is None or data.get('cooking_time') < 1:
            raise serializers.ValidationError({
                'cooking_time': 'Время приготовления должно быть больше 0.'
            })
        for ingredient in data.get('recipeingredient_set', []):
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0.'
                })
        return data

    def create_ingredients(self, ingredients, recipe):
        ingredient_list = []
        for ingredient_data in ingredients:
            ingredient = get_object_or_404(
                models.Ingredient, id=ingredient_data.get('id')
            )
            ingredient_list.append(
                models.RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data.get('amount')
                )
            )
        models.RecipeIngredient.objects.bulk_create(ingredient_list)

    @atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipeingredient_set', [])
        tags_data = validated_data.pop('tags', [])
        recipe = models.Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags_data)
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    @atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipeingredient_set', [])
        tags_data = validated_data.pop('tags', [])
        instance.tags.clear()
        instance.tags.set(tags_data)
        models.RecipeIngredient.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        self.create_ingredients(ingredients_data, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSerializer(
            instance,
            context={'request': request}
        ).data


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    author = UserSerializer()
    image = serializers.ImageField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return models.Favorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return models.ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False

    def get_ingredients(self, obj):
        ingredients = models.RecipeIngredient.objects.filter(recipe=obj)
        return IngredientGetSerializer(ingredients, many=True).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для работы со списком покупок."""
    class Meta:
        model = models.ShoppingCart
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=models.ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в список покупок'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeMiniSerializer(
            instance.recipe,
            context={'request': request}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для списка избранного."""
    class Meta:
        model = models.Favorite
        fields = '__all__'

    def validate(self, data):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            raise ValidationError({'status': 'Необходимо войти в систему.'})
        if models.Favorite.objects.filter(
            user=request.user, recipe=data['recipe']
        ).exists():
            raise ValidationError({'status': 'Рецепт уже есть в избранном.'})
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeMiniSerializer(
            instance.recipe, context={'request': request}
        ).data
