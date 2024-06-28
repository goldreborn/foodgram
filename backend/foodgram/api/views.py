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

from recipes import models
from .permissions import IsOwnerOrReadOnly, IsAuthenticatedUser
from .filters import IngredientFilter, RecipeFilter
from . import serializers


class TagViewSet(ReadOnlyModelViewSet):
    """
    ViewSet для тегов рецептов.

    Этот класс предоставляет операции чтения для тегов рецептов.
    Он использует TagSerializer для сериализации и десериализации тегов.
    """
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    ViewSet для ингредиентов.

    Получение информации об ингредиентах.
    """
    queryset = models.Ingredient.objects.all()
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
    queryset = models.Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticatedUser]
    )
    def add_to_favorites(self, request, pk=None):
        """
        Добавление рецепта в избранное.
        """
        recipe = self.get_object()
        favorite, created = models.Favorite.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        serializer = serializers.FavoriteSerializer(favorite)
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
    def remove_from_favorites(self, request, pk=None):
        """
        Удаление рецепта из избранного.
        """
        recipe = self.get_object()
        favorite = models.Favorite.objects.filter(
            user=request.user, recipe=recipe
        )
        favorite.delete()
        return Response({
            'message': 'Рецепт удален из избранного'
        }, status=status.HTTP_204_NO_CONTENT)

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticatedUser]
    )
    def add_to_shopping_list(self, request, pk=None):
        """
        Добавление рецепта в список покупок.
        """
        recipe = self.get_object()
        shopping_list, created = models.ShoppingList.objects.get_or_create(
            user=request.user, recipe=recipe
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
    def remove_from_shopping_list(self, request, pk=None):
        """
        Удаление рецепта из списка покупок.
        """
        recipe = self.get_object()
        shopping_list = models.ShoppingList.objects.filter(
            user=request.user, recipe=recipe
        )
        shopping_list.delete()
        return Response({
            'message': 'Рецепт удален из списка покупок'
        }, status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        """
        Создание нового рецепта.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class FavoriteViewSet(ModelViewSet):
    """
    ViewSet для избранного.

    Этот класс предоставляет CRUD-операции для избранного.
    Он использует FavoriteSerializer для сериализации
    и десериализации избранного.
    """
    queryset = models.Favorite.objects.all()
    serializer_class = serializers.FavoriteSerializer
    permission_classes = (IsAuthenticatedUser,)


class ShoppingListViewSet(ModelViewSet):
    """
    ViewSet для списка покупок.

    Этот класс предоставляет CRUD-операции для списка покупок.
    Он использует ShoppingListSerializer для сериализации
    и десериализации списка покупок.
    """
    queryset = models.ShoppingList.objects.all()
    serializer_class = serializers.ShoppingListSerializer
    permission_classes = (IsAuthenticatedUser,)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticatedUser])
    def download_shopping_list(self, request):
        """
        Скачивание списка покупок.
        """
        ingredients = {}
        for item in models.ShoppingList.objects.filter(user=request.user):
            for recipe_ingredient in item.recipe.recipeingredient_set.all():
                ingredient = recipe_ingredient.ingredient
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
