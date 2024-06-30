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
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from rest_framework import status
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.viewsets import (
    ModelViewSet, ReadOnlyModelViewSet, GenericViewSet
)
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from recipes import models
from .permissions import IsOwnerOrReadOnly, IsAuthenticatedUser
from .filters import IngredientFilter, RecipeFilter
from . import serializers


class TagViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    """Функция для модели тегов."""
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (AllowAny, )
    pagination_class = None


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
    queryset = models.Recipe.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers.RecipeCreateSerializer
        return serializers.RecipeSerializer

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        origin = 'https://edagram.zapto.org/api/recipes/'
        try:
            recipe = self.get_object()
            serializer = serializers.RecipeSerializer(recipe)
            return Response({
                'link': f'{origin}{serializer.data["id"]}/'
            }, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(
        detail=False,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticatedUser, ]
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            if models.Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response({
                    'message': 'Рецепт уже есть в избранном'
                }, status=status.HTTP_400_BAD_REQUEST)
            models.Favorite.objects.create(user=request.user, recipe=recipe)
            return Response({
                'message': 'Рецепт добавлен в избранное'
            }, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not models.Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response({
                    'message': 'Рецепт не в избранном'
                }, status=status.HTTP_400_BAD_REQUEST)
            models.Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).delete()
            return Response({
                'message': 'Рецепт удален из избранного'
            }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticatedUser])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            _, created = models.ShoppingCart.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if created:
                return Response({
                    'message': 'Recipe added to shopping cart'
                }, status=status.HTTP_201_CREATED)
            return Response({
                'message': 'Recipe already in shopping cart'
            }, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            models.ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).delete()
            return Response({
                'message': 'Recipe removed from shopping cart'
            }, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticatedUser, ]
    )
    def download_shopping_cart(self, request):
        """Отправка файла со списком покупок."""
        ingredients = models.RecipeIngredient.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount'))
        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            shopping_list.append(f'\n{name} - {amount}, {unit}')
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = \
            'attachment; filename="shopping_cart.txt"'
        return response
