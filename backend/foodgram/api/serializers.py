from django.db import transaction
from django.db.models import F
from .utils import Base64ImageField
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from users.models import Profile, Subscription
from recipes.models import (
    Ingredient,
    IngredientInRecipe,
    Recipe,
    Tag,
    ShoppingCart,
    Favourite
)


class ProfileSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user

        return (
            request and user.is_authenticated and Subscription.objects.filter(
                user=user, author=obj
            ).exists()
        )


class AvatarSerializer(ModelSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = Profile
        fields = ('avatar',)


class RecipeShortSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class UserSubscriptionSerializer(ProfileSerializer):
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'avatar', 'is_subscribed', 'recipes_count', 'recipes')
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                pass
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
        return serializer.data


class SubscriptionSerializer(ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        author = data['author']

        if user == author:
            raise ValidationError('Нельзя подписаться на самого себя')

        if Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError('Вы уже подписаны на данного пользователя')

        return data

    def to_representation(self, instance):
        return UserSubscriptionSerializer(
            instance.author,
            context=self.context
        ).data


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeReadSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = ProfileSerializer(read_only=True)
    ingredients = SerializerMethodField()
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id', 'name', 'measurement_unit',
            amount=F('ingredientinrecipe__amount')
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = request.user if request else None

        return (
            user and user.is_authenticated and user.favorites.filter(
                recipe=obj
            ).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user if request else None

        return (
            user and user.is_authenticated and user.shopping_cart.filter(
                recipe=obj
            ).exists())


class IngredientInRecipeWriteSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
        required=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeWriteSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    author = ProfileSerializer(read_only=True)
    ingredients = IngredientInRecipeWriteSerializer(many=True, required=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        validated_data = super().validate(data)

        if not validated_data.get('image'):
            raise ValidationError(
                {'image': 'Не предоставлена картинка рецепта'}
            )

        ingredients = validated_data.get('ingredients', [])

        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Нужен хотя бы один ингредиент'}
            )

        ingredients_list = []

        for ingredient in ingredients:

            if ingredient in ingredients_list:
                raise ValidationError(
                    {'ingredients': 'Ингредиенты не могут повторяться'}
                )

            ingredients_list.append(ingredient)

        tags = validated_data.get('tags', [])

        if not tags:
            raise ValidationError(
                {'tags': 'Нужно выбрать хотя бы один тег!'}
            )

        tags_list = []

        for tag in tags:
            if tag in tags_list:
                raise ValidationError(
                    {'tags': 'Теги должны быть уникальными!'}
                )
            tags_list.append(tag)

        return validated_data

    @staticmethod
    @transaction.atomic
    def create_ingredients_amounts(ingredients, recipe):
        ingredient_instances = [
            IngredientInRecipe(
                ingredient=ingredient['ingredient'],
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ]
        IngredientInRecipe.objects.bulk_create(ingredient_instances)

    def create(self, validated_data):
        request = self.context.get('request')
        author = request.user

        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amounts(
            recipe=recipe,
            ingredients=ingredients
        )

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        instance.tags.clear()
        instance.ingredients.clear()

        instance.tags.set(tags)
        self.create_ingredients_amounts(ingredients, instance)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeReadSerializer(instance, context=context).data


class FavoriteSerializer(ModelSerializer):
    class Meta:
        model = Favourite
        fields = ('user', 'recipe',)

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if user.favorites.filter(recipe=recipe.id).exists():
            raise ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if user.shopping_cart.filter(recipe=recipe.id).exists():
            raise ValidationError(
                'Рецепт уже добавлен в корзину'
            )
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
