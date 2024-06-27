"""
Модуль для работы с рецептами и связанными с ними данными.

В этом модуле определены ViewSet для тегов, пользователей,
рецептов, избранного, подписок и списка покупок.

Он предоставляет функциональность для создания, чтения,
обновления и удаления данных о рецептах, а также для управления
избранными рецептами, подписками на авторов и списками покупок.

Каждый ViewSet предоставляет набор методов для выполнения операций с данными.
"""
from django.http import HttpResponse
from django.db.transaction import atomic
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from recipes.models import Tag, Recipe, Ingredient, Favorites, ShoppingList
from .permissions import IsOwnerOrReadOnly, IsAuthenticatedUser
from .filters import IngredientFilter, RecipeFilter
from . import serializers


class TagViewSet(ModelViewSet):
    """
    ViewSet для тегов рецептов.

    Этот класс предоставляет CRUD-операции для тегов рецептов.
    Он использует TagSerializer для сериализации и десериализации тегов.
    """
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    ViewSet для ингредиентов.

    Получение информации о ингредиенте.
    """
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """
    ViewSet для рецептов.

    Этот класс предоставляет CRUD-операции для рецептов.
    Он использует RecipeSerializer для сериализации и десериализации рецептов.
    """
    queryset = Recipe.objects.all().order_by('-pub_date')
    serializer_class = serializers.RecipeSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticatedUser]
    )
    def add_to_favorites(self, request, pk):
        """
        Добавление рецепта в избранное.
        """
        favorite, created = Favorites.objects.get_or_create(
            user=request.user, recipe=self.get_object()
        )
        serializer = serializers.FavoritesSerializer(favorite)
        if created:
            return Response({
                'message': 'Рецепт добавлен в избранное',
                'data': serializer.data
            })
        return Response({
            'message': 'Рецепт уже находится в избранном',
            'data': serializer.data
        })

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticatedUser]
    )
    def remove_from_favorites(self, request, pk):
        """
        Удаление рецепта из избранного.
        """
        favorite = Favorites.objects.filter(
            user=request.user, recipe=self.get_object()
        )
        favorite.delete()
        return Response({
            'message': 'Рецепт удален из избранного'
        }, status=status.HTTP_204_NO_CONTENT)

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticatedUser]
    )
    def add_to_shopping_list(self, request, pk):
        """
        Добавление рецепта в список покупок.
        """
        shopping_list, created = ShoppingList.objects.get_or_create(
            user=request.user, recipe=self.get_object()
        )
        serializer = serializers.ShoppingListSerializer(shopping_list)
        if created:
            return Response({
                'message': 'Рецепт добавлен в список покупок',
                'data': serializer.data
            })
        return Response({
            'message': 'Рецепт уже находится в списке покупок',
            'data': serializer.data
        })

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticatedUser]
    )
    def remove_from_shopping_list(self, request, pk):
        """
        Удаление рецепта из списка покупок.
        """
        shopping_list = ShoppingList.objects.filter(
            user=request.user, recipe=self.get_object()
        )
        shopping_list.delete()
        return Response({
            'message': 'Рецепт удален из списка покупок'
        }, status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        """
        Создание нового рецепта.
        """
        tags = request.data.get('tags', [])
        ingredients = request.data.get('ingredients', [])
        image = request.FILES.get('image')

        recipe = Recipe(
            name=request.data.get('name'),
            author=request.user,
            text=request.data.get('text'),
            cooking_time=request.data.get('cooking_time')
        )
        recipe.save()

        for tag in tags:
            tag_obj, _ = Tag.objects.get_or_create(name=tag)
            recipe.tags.add(tag_obj)

        for ingredient in ingredients:
            ingredient_obj, _ = Ingredient.objects.get_or_create(
                name=ingredient['name']
            )
            recipe.ingredients.add(ingredient_obj)

        if image:
            recipe.image = image
            recipe.save()

        serializer = serializers.RecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FavoritesViewSet(ModelViewSet):
    """
    ViewSet для избранного.

    Этот класс предоставляет CRUD-операции для избранного.
    Он использует FavoritesSerializer для сериализации
    и десериализации избранного.
    """
    queryset = Favorites.objects.all()
    serializer_class = serializers.FavoritesSerializer
    permission_classes = (IsAuthenticatedUser,)


class ShoppingListViewSet(ModelViewSet):
    """
    ViewSet для списка покупок.

    Этот класс предоставляет CRUD-операции для списка покупок.
    Он использует ShoppingListSerializer для сериализации
    и десериализации списка покупок.
    """
    queryset = ShoppingList.objects.all()
    serializer_class = serializers.ShoppingListSerializer
    permission_classes = (IsAuthenticatedUser,)

    @action(methods=['get'], detail=False)
    def download_shopping_list(self, request):
        """
        Скачивание списка покупок.
        """
        ingredients = {}
        for item in ShoppingList.objects.filter(user=request.user):
            for recipe_ingredient in item.recipe.recipeingredient_set.all():
                ingredient = recipe_ingredient.ingredients
                quantity = recipe_ingredient.amount
                if ingredient.name in ingredients:
                    ingredients[ingredient.name] += quantity
                else:
                    ingredients[ingredient.name] = quantity

        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        for ingredient, quantity in ingredients.items():
            response.write(f'{ingredient} - {quantity}\n')
        return response
