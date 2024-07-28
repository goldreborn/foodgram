"""
Модуль сериализаторов для рецептов и связанных с ними данных.

В этом модуле определены сериализаторы для тегов, пользователей,
рецептов, избранного, подписок и списка покупок.

Сериализаторы используются для преобразования данных в формат,
подходящий для передачи по сети или хранения в базе данных.
"""

from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from djoser import serializers as djoser_serializers
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes import models
from .utils import Base64ImageField
from users.models import User, Subscription


class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )
        extra_kwargs = {'password': {'write_only': True}}


class UserSerializer(djoser_serializers.UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(djoser_serializers.UserSerializer.Meta):
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False

    def update(self, instance, validated_data):
        if 'avatar' in validated_data:
            instance.avatar = validated_data['avatar']
            instance.save()
        return super().update(instance, validated_data)


class UserSubscribeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='author.email')
    id = serializers.IntegerField(source='author.id')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source='author.avatar')

    class Meta:
        model = Subscription
        fields = [
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        ]

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit', None
        )
        recipes = obj.author.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()


class UserSubscriptionsListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='author.email')
    id = serializers.IntegerField(source='author.id')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source='author.avatar')

    class Meta:
        model = Subscription
        fields = [
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        ]

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit', None
        )
        recipes = obj.author.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами."""
    class Meta:
        model = models.Ingredient
        fields = ('id', 'name', 'measurement_unit',)


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
        many=True, source='recipeingredients'
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
        if not data.get('tags'):
            raise serializers.ValidationError({
                'tags': 'Теги должны быть указаны.'
            })
        if len(data.get('tags', [])) != len(set(data.get('tags', []))):
            raise serializers.ValidationError({
                'tags': 'Теги должны быть уникальными.'
            })
        for tag in data.get('tags', []):
            if not models.Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError({
                    'tags': 'Несуществующий тег.'
                })
        if not data.get('image'):
            raise serializers.ValidationError({
                'image': 'Изображение должно быть указано.'
            })
        ingredients = data.get('recipeingredients', [])
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты должны быть указаны.'
            })
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты должны быть уникальными.'
            })
        for ingredient in ingredients:
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0.'
                })
            if not models.Ingredient.objects.filter(
                id=ingredient['id']
            ).exists():
                raise serializers.ValidationError({
                    'ingredients': 'Несуществующий ингредиент.'
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
        ingredients_data = validated_data.pop('recipeingredients', [])
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
        ingredients_data = validated_data.pop('recipeingredients', [])
        tags_data = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.ingredients.clear()
        self.create_ingredients(ingredients_data, instance)
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSerializer(
            instance, context={'request': request}
        ).data


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = models.Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_ingredients(self, obj):
        return IngredientGetSerializer(
            models.RecipeIngredient.objects.filter(recipe=obj), many=True
        ).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated and models.Favorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user
        return (
            user.is_authenticated and models.ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    def get_short_link(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(f'/recipes/{obj.id}/short/')


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с избранным."""
    class Meta:
        model = models.Favorite
        fields = ('id', 'name', 'image', 'cooking_time')
        validators = [
            UniqueTogetherValidator(
                queryset=models.Favorite.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже в избранном'
            )
        ]

    def validate(self, data):
        request = self.context.get('request')
        if models.Favorite.objects.filter(
            user=request.user, recipe=data['recipe']
        ).exists():
            raise ValidationError('Рецепт уже в избранном.')
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeMiniSerializer(
            instance.recipe, context={'request': request}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для работы со списком покупок."""
    class Meta:
        model = models.ShoppingCart
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=models.ShoppingCart.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже в списке покупок'
            )
        ]

    def validate(self, data):
        request = self.context.get('request')
        if models.ShoppingCart.objects.filter(
            user=request.user, recipe=data['recipe']
        ).exists():
            raise ValidationError('Рецепт уже в списке покупок.')
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeMiniSerializer(
            instance.recipe, context={'request': request}
        ).data
