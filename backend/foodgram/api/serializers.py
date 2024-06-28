"""
Модуль сериализаторов для рецептов и связанных с ними данных.

В этом модуле определены сериализаторы для тегов, пользователей,
рецептов, избранного, подписок и списка покупок.

Сериализаторы используются для преобразования данных в формат,
подходящий для передачи по сети или хранения в базе данных.
"""
from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from djoser import serializers as djoser_serializers
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes import models
from .utils import Base64ImageField
from users.models import User, Subscription


class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    """Сериализатор для регистрации пользователей."""
    avatar = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password', 'avatar'
        )


class UserSerializer(djoser_serializers.UserSerializer):
    """Сериализатор для работы с информацией о пользователях."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)
    avatar_url = serializers.SerializerMethodField(
        'get_avatar_url',
        read_only=True,
    )

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

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
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')
        read_only_fields = (
            'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
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


class UserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['avatar']

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class UserSubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки/отписки от пользователей."""
    class Meta:
        model = Subscription
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
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


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""
    class Meta:
        model = models.Tag
        fields = '__all__'


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


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецептов"""
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientGetSerializer(
        many=True, source='recipeingredients'
    )
    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = models.Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        auth = request.user.is_authenticated
        return (request and auth and models.Favorite.objects.filter(
                    user=request.user, recipe=obj
                ).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated and
                models.ShoppingList.objects.filter(
                    user=request.user, recipe=obj
                ).exists())


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=models.Tag.objects.all(), many=True
    )
    ingredients = IngredientPostSerializer(
        many=True, source='recipeingredients'
    )
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = models.Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        )

    def validate(self, data):
        """Метод валидации данных рецепта."""
        if data.get('cooking_time') < 0:
            raise ValidationError(
                {'cooking_time': 'Время приготовления не может быть меньше 0'}
            )
        for ingredient in data.get('recipeingredients'):
            if ingredient.get('amount') <= 0:
                raise ValidationError(
                    'Количество ингредиента не может быть меньше 0'
                )
        return data

    @staticmethod
    def create_ingredients(ingredients, recipe):
        ingredient_list = []
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                models.Ingredient, id=ingredient.get('id')
            )
            ingredient_list.append(models.RecipeIngredient(
                recipe=recipe,
                ingredient=current_ingredient,
                amount=ingredient.get('amount')
            ))
        models.RecipeIngredient.objects.bulk_create(ingredient_list)

    @atomic
    def create(self, validated_data):
        tags_data = self.context['request'].data.get('tags', [])
        ingredients_data = self.context['request'].data.get('ingredients', [])
        recipe = models.Recipe.objects.create(**validated_data)

        for tag_id in tags_data:
            tag = models.Tag.objects.get(id=tag_id)
            recipe.tags.add(tag)

        for ingredient_data in ingredients_data:
            ingredient_name = ingredient_data.get('name')
            amount = ingredient_data.get('amount')
            measurement_unit = ingredient_data.get('measurement_unit')

            ingredient, _ = models.Ingredient.objects.get_or_create(
                name=ingredient_name
            )
            models.RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount,
                measurement_unit=measurement_unit
            )

        return recipe

    @atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipeingredients')
        instance.tags.clear()
        instance.tags.set(tags)
        models.RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_ingredients(ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSerializer(instance, context={'request': request}).data


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор для работы со списком покупок."""
    class Meta:
        model = models.ShoppingList
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=models.ShoppingList.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в список покупок'
            )
        ]


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для списка избранного."""
    class Meta:
        model = models.Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            raise ValidationError({'status': 'Необходимо войти в систему.'})
        if models.Favorite.objects.filter(
            user=request.user, recipe=data['recipe']
        ).exists():
            raise ValidationError({'status': 'Рецепт уже есть в избранном.'})
        return data
